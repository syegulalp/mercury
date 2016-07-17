function notify(message) {
  if (!("Notification" in window)) {
    alert("This browser does not support desktop notification.");
  }

  else if (Notification.permission === "granted") {
    _notify(message);
  }

  else if (Notification.permission !== 'denied') {
    Notification.requestPermission(function (permission) {
      // If the user accepts, let's create a notification
      if (permission === "granted") {
        _notify(message);
      }
    });
  }
}

function _notify(message){
    var notification = new Notification(message);   
}