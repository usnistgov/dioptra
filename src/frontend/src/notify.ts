import { Notify } from 'quasar';

export function success(message: string) {
  return Notify.create({
    color: 'green-7',
    textColor: 'white',
    icon: 'done',
    message: message
  });
}

export function error(message: string) {
  return Notify.create({
    color: 'red-5',
    textColor: 'white',
    icon: 'warning',
    message: message
  });
}

export function wait(message: string) {
  return Notify.create({
    color: 'blue-5',
      textColor: 'white',
      spinner: true,
      message: message,
	    timeout: 0 //intended to be dismissed manually
  });
}
