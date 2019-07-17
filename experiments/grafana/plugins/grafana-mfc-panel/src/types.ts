export interface Options {
  setPoint: number;
  flowRate: number;
}

export const defaults: Options = {
  setPoint: 1.5,
  flowRate: 200
};

export interface MyProps {
  options: Options
}
