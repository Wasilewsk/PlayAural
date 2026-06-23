window.PLAYAURAL_WEB_VERSION = "1.0.4.5";

import("./app.js").catch((error) => {
  console.error("PlayAural web client failed to start.", error);
  const target = document.getElementById("live-assertive") || document.body;
  const message = document.createElement("p");
  message.textContent = "PlayAural web client failed to start. Please refresh this page.";
  target.appendChild(message);
});
