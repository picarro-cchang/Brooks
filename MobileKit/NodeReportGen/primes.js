function nextPrime(n) {
    var smaller;
    n = Math.floor(n);
    if (n >= 2) {
        smaller = 1;
        while (smaller * smaller <= n) {
            n += 1;
            smaller = 2;
            while ((n % smaller > 0) && (smaller * smaller <= n)) {
                smaller += 1;
            }
        }
        return n;
    }
    else {
        return 2;
    }
}

function asyncPrime(n, fn) {
    setTimeout(function () {
        fn(nextPrime(n));
    }, 10);
}

exports.nextPrime = nextPrime;
exports.asyncPrime = asyncPrime;
