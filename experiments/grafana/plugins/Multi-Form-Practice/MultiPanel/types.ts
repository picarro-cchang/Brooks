
export interface Options {
  fName: string;
  lName: string;
  age: number;
  gender: string;
  imageUrl: string;
}

export interface ExtraOptions {
  layout: string;
  formOptions: Options;
}

export const defaults: ExtraOptions = {
  layout: "bigform",
  formOptions: {
    fName: "",
    lName: "",
    age: null,
    gender: "",
    imageUrl: "https://images.unsplash.com/photo-1518791841217-8f162f1e1131?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&w=1000&q=80"
  }
};

export interface MyProps {
  options: ExtraOptions;
}
