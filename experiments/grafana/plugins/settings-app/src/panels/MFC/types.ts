export interface Options {
  set_point: number;
  flow_rate: number;
}

export const defaults: Options = {
  set_point: 0,
  flow_rate: 0
};

export interface MyProps {
  options: Options
}
