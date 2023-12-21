import { Notify } from 'quasar';

export function success(message: string) {
  Notify.create({
    color: 'green-7',
    textColor: 'white',
    icon: 'done',
    message: message
  });
}

export function error(message: string) {
  Notify.create({
    color: 'red-5',
      textColor: 'white',
      icon: 'warning',
      message: message
  });
}