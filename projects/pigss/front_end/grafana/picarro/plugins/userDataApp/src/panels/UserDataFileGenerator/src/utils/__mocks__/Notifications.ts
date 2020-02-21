
export const notifyError = (message: string) => {
  return ('ERROR '+ message);
};

export const notifySuccess = (message: string) => {
  console.log('SUCCESS ', message);

};
