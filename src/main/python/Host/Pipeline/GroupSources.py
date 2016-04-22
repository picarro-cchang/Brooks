import itertools
import numpy as np

from traitlets import (Bool, Enum, Float, HasTraits, Instance, Integer)
from traitlets.config import (Configurable,)

class CompositeVerdict(Configurable):
    state = Enum(['NONE', 'POSSIBLE_NATURAL_GAS', 'NOT_NATURAL_GAS', 'NATURAL_GAS'], default_value="NONE")
    ethane_ratio = Float(0.0)
    ethane_ratio_sdev = Float(0.0)
    confidence = Float(0.0)

    def __init__(self, **kwargs):
        super(CompositeVerdict, self).__init__(**kwargs)
        bad_kwargs = set(kwargs.keys()).difference(CompositeVerdict.class_trait_names())
        if bad_kwargs:
            raise ValueError, "Unrecognized keyword argument(s): %s" % (", ".join(bad_kwargs))
        self.state = 'NONE'

    def add_result(self, verdict, ethane_ratio, ethane_ratio_sdev, confidence):
        def replace_values():
            self.state = verdict
            self.ethane_ratio = ethane_ratio
            self.ethane_ratio_sdev = ethane_ratio_sdev
            self.confidence = confidence
        if self.state == 'NONE':
            replace_values()
        elif self.state == 'POSSIBLE_NATURAL_GAS':
            if verdict == 'NATURAL_GAS':
                replace_values()
            elif (verdict == 'POSSIBLE_NATURAL_GAS') and (self.confidence < confidence):
                replace_values()
        elif self.state == 'NOT_NATURAL_GAS':
            if verdict in ['POSSIBLE_NATURAL_GAS', 'NATURAL_GAS']:
                replace_values()
            elif (verdict == 'NOT_NATURAL_GAS') and (self.ethane_ratio_sdev > ethane_ratio_sdev):
                replace_values()
        elif self.state == 'NATURAL_GAS':
            if (verdict == 'NATURAL_GAS') and (self.ethane_ratio_sdev > ethane_ratio_sdev):
                replace_values()
        else:
            raise ValueError("Bad state", self.state)

class SourceAggregator(Configurable):
    """Calculate the best ways of aggregating the given measurements
       and uncertainties into a number of sources"""
    measurements = Instance(np.ndarray)
    uncertainties = Instance(np.ndarray)
    max_candidates = Integer(5)
    max_sources = Integer(5)
    prior_prob_factor_per_source = Float(0.2)
    source_range = Float(1.0)
    ignore_source_range = Bool(False)

    def __init__(self, **kwargs):
        super(SourceAggregator, self).__init__(**kwargs)
        bad_kwargs = set(kwargs.keys()).difference(SourceAggregator.class_trait_names())
        if bad_kwargs:
            raise ValueError, "Unrecognized keyword argument(s): %s" % (", ".join(bad_kwargs))

    def is_canonical(self, sources, num_sources):
        max_sources = -1
        for source in sources:
            if source - max_sources > 1:
                return False
            max_sources = max(max_sources, source)
        return max_sources == num_sources-1

    def group_stats(self, sources):
        num_sources = max(sources) + 1
        weights = np.zeros(num_sources)
        totals = np.zeros(num_sources)
        for meas_num, source in enumerate(sources):
            weight = self.uncertainties[meas_num]**(-2)
            weights[source] += weight
            totals[source] += self.measurements[meas_num]*weight
        group_means = totals/weights
        group_uncertainties = 1.0/np.sqrt(weights)
        return group_means, group_uncertainties

    def weighted_combination(self, measurements, uncertainties):
        weights = uncertainties**(-2)
        wtot = sum(weights)
        average = sum(weights * measurements)/wtot
        uncertainty = wtot**(-0.5)
        return average, uncertainty

    def aggregate(self):
        """Calculate the probabilities of various ways in which the measurements may be distributed
            among sources.
        The result is a list of hypotheses in order of decreasing probability, where each
            hypothesis is a 3-tuple:

        Item 0: is the relative probability of the hypothesis
        Item 1: is the number of sources in the hypothesis
        Item 2: is the tuple specifying the assigment of the measurements to the sources

        The method get_assignment may be used to extract the information within a hypothesis
            in a more convenient form
        """
        assert len(self.measurements) == len(self.uncertainties)
        num_measurements = len(self.measurements)

        if num_measurements > self.max_candidates:
            perm = np.argsort(self.measurements)
            measurements_sorted = self.measurements[perm]
            uncertainties_sorted = self.uncertainties[perm]
            while len(measurements_sorted) > self.max_candidates:
                # Find measurements that are closest together and coalasce them
                closest = np.argmin(np.diff(measurements_sorted))
                average, uncertainty = self.weighted_combination(measurements_sorted[closest:closest+2], uncertainties_sorted[closest:closest+2])
                measurements_sorted = np.concatenate((measurements_sorted[:closest], [average], measurements_sorted[closest+2:]))
                uncertainties_sorted = np.concatenate((uncertainties_sorted[:closest], [uncertainty], uncertainties_sorted[closest+2:]))
            self.measurements = measurements_sorted
            self.uncertainties = uncertainties_sorted
            num_measurements = len(self.measurements)

        prior = self.prior_prob_factor_per_source ** np.arange(num_measurements + 1)

        merit = {}
        max_merit = -float('inf')
        num_sources_max = min(num_measurements, self.max_sources)

        for num_sources in range(1, num_sources_max+1):
            merit[num_sources] = {}
            # Iterate through ways of dividing the measurements among the sources
            for sources in itertools.product(range(num_sources), repeat=num_measurements):
                if self.is_canonical(sources, num_sources):
                    group_means, group_uncertainties = self.group_stats(sources)
                    # Calculate merit in terms of log probabilities to avoid overflow
                    if self.ignore_source_range:
                        merit[num_sources][sources] = (np.log(prior[num_sources]) +
                                                       0.5*np.sum((group_means/group_uncertainties)**2))
                    else:
                        merit[num_sources][sources] = (np.log(prior[num_sources] *
                                                              (np.sqrt(2 * np.pi) / self.source_range) ** num_sources *
                                                              np.prod(group_uncertainties)) +
                                                       0.5*np.sum((group_means/group_uncertainties)**2))
                    #merit[num_sources][sources] = (np.log(prior[num_sources] *
                    #                                      (np.sqrt(2 * np.pi) / self.source_range) ** num_sources) +
                    #                               0.5*np.sum((group_means/group_uncertainties)**2))
            for sources in merit[num_sources]:
                merit[num_sources][sources] -= np.log(len(merit[num_sources]))
                max_merit = max(max_merit, merit[num_sources][sources])

        # Exponentiate the merit
        for num_sources in range(1, num_sources_max+1):
            for sources in merit[num_sources]:
                merit[num_sources][sources] = np.exp(merit[num_sources][sources] - max_merit)

        # Calculate probabilities of different numbers of sources
        prob_num = {}
        for num_sources in range(1, num_sources_max + 1):
            prob_num[num_sources] = sum(merit[num_sources].values())
        tot_prob = sum(prob_num.values())
        for num_sources in range(1, num_sources_max+1):
            prob_num[num_sources] /= tot_prob
        # Find hypotheses with largest values of merit
        hypotheses = []
        for num_sources in range(1, num_sources_max+1):
            for key in merit[num_sources]:
                hypotheses.append((merit[num_sources][key]/tot_prob, num_sources, key))
        hypotheses.sort()
        hypotheses.reverse()
        return hypotheses

    def get_assignment(self, hypothesis):
        """Return a dictionary giving details about a hypothesis. The keys are:
               probability: The posterior probability of the hypothesis
               groups: A list of dictionaries specifying how the measurements are grouped into sources
           Each group dictionary has the following keys:
               measurements: A list of the measurement indices (1-origin) which are in this group
               mean: The weighted mean of the measurements in the group
               uncertainty: The weighted standard error of the mean of the measurements in the group
        """
        prob, num_sources, assignment = hypothesis
        source_means, source_uncertainties = self.group_stats(assignment)
        groups = []
        for i in range(num_sources):
            members = [j+1 for j in range(len(self.measurements)) if assignment[j] == i]
            groups.append(dict(measurements=members, mean=source_means[i], uncertainty=source_uncertainties[i]))
        return dict(probability=prob, groups=groups)

    def dump(self, hypothesis):
        """Print out details of an assigment of measurements among sources
               specified by a hypothesis.
        """
        assignment = self.get_assignment(hypothesis)
        print "Probability %.3g: %d sources" % (assignment["probability"], len(assignment["groups"]))
        for i, group in enumerate(assignment["groups"]):
            print "Source %d %s: %g +/- %g" % (i, group["measurements"], group["mean"], group["uncertainty"])

if __name__ == "__main__":
    measurements = np.array([-0.038, 0.008, 0.005, 0.008, 0.009, 0.004, 0.038])
    uncertainties = np.array([0.005, 0.005, 0.007, 0.005, 0.005, 0.003, 0.004])
    sa = SourceAggregator(measurements=measurements, uncertainties=uncertainties, max_candidates=len(measurements))
    hypotheses = sa.aggregate()
    print "Most likely Hypotheses"
    print "======================"
    for hypothesis in hypotheses[:5]:
        sa.dump(hypothesis)
