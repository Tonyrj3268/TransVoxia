function showMessage(message) {
  var messageElement = document.getElementById("message");
  messageElement.innerHTML = message;
}

var xhr = new XMLHttpRequest();
xhr.onreadystatechange = function() {
  if (this.readyState == 4 && this.status == 200) {
    var response = JSON.parse(this.responseText);
    if (response.status == "success") {
      showMessage(response.message);
    } else {
      showMessage(response.message);
    }
  }
};

var form = document.querySelector("form");

