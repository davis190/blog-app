(function () {
    var API = "https://api.blog.claytondavis.dev/prod/api/email";

    function setMessage(el, message, isError) {
        el.textContent = message;
        el.classList.toggle("error", !!isError);
    }

    // The "Get new posts by email" box. Subscribing only sends a confirmation email.
    function initSubscribe(form) {
        var input = form.querySelector("input");
        var button = form.querySelector("button");
        var status = form.parentNode.querySelector(".subscribe-status");

        form.addEventListener("submit", function (e) {
            e.preventDefault();
            var email = input.value.trim();
            if (!email) {
                setMessage(status, "Please enter your email address.", true);
                return;
            }

            button.disabled = true;
            setMessage(status, "Subscribing...", false);
            fetch(API + "/subscribe", { method: "POST", body: email })
                .then(function (res) {
                    if (!res.ok) { throw new Error(res.status); }
                    input.value = "";
                    setMessage(status, "Almost done! Check your inbox for a link to confirm your subscription.", false);
                })
                .catch(function () {
                    setMessage(status, "That doesn't look like a valid email. Please check it and try again.", true);
                })
                .then(function () { button.disabled = false; });
        });
    }

    // Pages reached from a link in an email (/confirm/ and /unsubscribe/). Nothing happens
    // until the button is clicked, so a mail scanner that merely opens the link can't act.
    var ACTIONS = {
        confirm: {
            param: "token",
            method: "POST",
            path: "/confirm",
            prompt: function (who) { return who ? "Confirm your subscription for " + who + "?" : "Confirm your subscription?"; },
            button: "Confirm subscription",
            done: "You're subscribed. Thanks for confirming!",
            invalid: "This confirmation link is invalid or has expired. Please subscribe again from the blog."
        },
        unsubscribe: {
            param: "token",
            legacyParam: "email", // links in emails sent before signed links existed
            method: "DELETE",
            path: "/unsubscribe",
            prompt: function (who) { return who ? "Unsubscribe " + who + " from new post emails?" : "Unsubscribe from new post emails?"; },
            button: "Unsubscribe",
            done: "You've been unsubscribed. Come back soon!",
            invalid: "This unsubscribe link is invalid. Please use the link in the most recent email, or email blog@claytondavis.dev."
        }
    };

    function queryParam(name) {
        var match = window.location.search.match(new RegExp("[?&]" + name + "=([^&]*)"));
        // Not URLSearchParams: it would turn the "+" in an address like a+b@x.com into a space.
        return match ? decodeURIComponent(match[1]).trim() : "";
    }

    // The address a signed token was issued for, for display only. The server checks the signature.
    function addressInToken(token) {
        try {
            var payload = token.split(".")[0].replace(/-/g, "+").replace(/_/g, "/");
            return JSON.parse(atob(payload)).e || "";
        } catch (e) {
            return "";
        }
    }

    function initEmailAction(panel) {
        var config = ACTIONS[panel.getAttribute("data-action")];
        var message = panel.querySelector(".email-action-message");
        var button = panel.querySelector(".email-action-button");
        if (!config) { return; }

        var value = queryParam(config.param);
        var who = addressInToken(value);
        if (!value && config.legacyParam) {
            value = who = queryParam(config.legacyParam);
        }
        if (!value) {
            setMessage(message, config.invalid, true);
            return;
        }

        setMessage(message, config.prompt(who), false);
        button.textContent = config.button;
        button.hidden = false;

        button.addEventListener("click", function () {
            button.disabled = true;
            setMessage(message, "Working...", false);
            fetch(API + config.path, { method: config.method, body: value })
                .then(function (res) {
                    if (res.ok) {
                        button.hidden = true;
                        setMessage(message, config.done, false);
                    } else {
                        button.hidden = true;
                        setMessage(message, config.invalid, true);
                    }
                })
                .catch(function () {
                    button.disabled = false;
                    setMessage(message, "Something went wrong. Please try again.", true);
                });
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll(".subscribe-form").forEach(initSubscribe);
        document.querySelectorAll(".email-action").forEach(initEmailAction);
    });
})();
