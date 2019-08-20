import React from 'react';
import { Select, FormLabel } from '@grafana/ui';

export default function SelectFilter() {
  // @ts-ignore
  const { classes, title, labelWidth, selectWidth, selectOptions, optionsChange, defaultValue, val } = this.props;
  return (
    <div className="gf-form col-md-3 col-sm-3">
      <FormLabel width={labelWidth}>{title}</FormLabel>
      <Select
        width={selectWidth}
        options={selectOptions}
        onChange={optionsChange}
        value={selectOptions.find((option: any) => option.value === val)}
        defaultValue={defaultValue}
        backspaceRemovesValue
        isLoading
      />
    </div>
  );
}
