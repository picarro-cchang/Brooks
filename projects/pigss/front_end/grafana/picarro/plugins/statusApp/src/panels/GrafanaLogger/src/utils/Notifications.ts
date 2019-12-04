import { toast } from 'react-toastify';

export const notifyError = (message: string) => {
  console.error(message);
  toast.error(message, {
    position: 'bottom-right',
    autoClose: 8000,
    hideProgressBar: false,
    closeOnClick: true,
    pauseOnHover: true,
    draggable: true,
  });
};

export const notifySuccess = (message: string) => {
  toast.success(message, {
    position: 'bottom-right',
    autoClose: 8000,
    hideProgressBar: false,
    closeOnClick: true,
    pauseOnHover: true,
    draggable: true,
  });
};
