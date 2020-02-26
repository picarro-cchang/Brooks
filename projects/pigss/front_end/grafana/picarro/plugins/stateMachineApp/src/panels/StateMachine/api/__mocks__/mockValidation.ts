const validate = (plan: any) => {
  if (plan.last_step <= 0) {
    return Error("Plan is empty");
  }
  if (plan.current_step < 1 || plan.current_step >= plan.last_step) {
    return Error("Pending Step must be in between 1 and " + plan.last_step);
  }
  for (let i = 0; i < plan.last_step; i++) {
    const row = i + 1;
    const s = plan.steps[row.toString()];
    if (!("duration" in s) || !("reference" in s) || !("banks" in s)) {
      return Error("Malformed Data");
    }
    if (!(s.duration > 0 || s.duration < 20)) {
      return Error("Duration must be greater than 20");
    }
    for (const bank in s.banks) {
      if (!["1", "3", "4"].includes(bank)) {
        return Error("Invalid Bank");
      }
      const bank_config = s.banks[bank];
      if (!("chan_mask" in bank_config) || !("clean" in bank_config)) {
        return Error("Invalid data for bank");
      }
      if (!(0 <= bank_config.chan_mask && bank_config.chan_mask < 256)) {
        return Error("Invalid channel selection for bank");
      }
    }
  }
  return true;
};

export default validate;
