document.addEventListener("click", function (event) {
  var target = event.target;
  var button = target.closest("[data-password-toggle]");
  if (!button) {
    return;
  }

  var group = button.closest(".password-input-group");
  var input = group && group.querySelector("input");
  var icon = button.querySelector("i");
  if (!input || !icon) {
    return;
  }

  var showPassword = input.type === "password";
  input.type = showPassword ? "text" : "password";
  button.setAttribute("aria-label", showPassword ? "Hide password" : "Show password");
  button.setAttribute("aria-pressed", String(showPassword));
  icon.className = showPassword ? "bi bi-eye" : "bi bi-eye-slash";
});

// Fade out success/info messages after a few seconds (errors stay until closed)
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".cm-alert.alert-success, .cm-alert.alert-info").forEach(function (el) {
    setTimeout(function () {
      bootstrap.Alert.getOrCreateInstance(el).close();
    }, 6000);
  });

  // Portfolio lightbox: fill the modal with the clicked image
  var box = document.getElementById("lightbox");
  if (box) {
    box.addEventListener("show.bs.modal", function (event) {
      var trigger = event.relatedTarget;
      document.getElementById("lightbox-img").src = trigger.getAttribute("data-src");
      document.getElementById("lightbox-caption").textContent = trigger.getAttribute("data-caption") || "";
    });
  }

  initializeTimePickers();
});

function initializeTimePickers() {
  document.querySelectorAll("input[data-time-picker]").forEach(function (input) {
    var form = input.form;
    if (!form) {
      return;
    }

    var wrapper = document.createElement("div");
    wrapper.className = "input-group time-picker-group";
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    var trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "btn btn-time-picker";
    trigger.setAttribute("aria-label", "Choose time");
    trigger.setAttribute("aria-haspopup", "dialog");
    trigger.setAttribute("aria-expanded", "false");
    var icon = document.createElement("i");
    icon.className = "bi bi-clock";
    icon.setAttribute("aria-hidden", "true");
    trigger.appendChild(icon);
    wrapper.appendChild(trigger);

    var popup = document.createElement("div");
    popup.className = "cm-time-picker";
    popup.id = input.id + "_picker";
    popup.setAttribute("role", "dialog");
    popup.setAttribute("aria-label", "Choose a time");

    var heading = document.createElement("div");
    heading.className = "cm-time-picker-heading";
    heading.textContent = "Choose a time";
    popup.appendChild(heading);

    var controls = document.createElement("div");
    controls.className = "cm-time-picker-controls";
    var hour = createTimeInput("Hour", 1, 12);
    var minute = createTimeInput("Minute", 0, 59);
    var period = createTimeSelect("AM/PM", ["AM", "PM"]);
    controls.appendChild(hour.container);
    controls.appendChild(minute.container);
    controls.appendChild(period.container);
    popup.appendChild(controls);

    var validationMessage = document.createElement("div");
    validationMessage.className = "cm-time-picker-error";
    validationMessage.id = popup.id + "_error";
    validationMessage.setAttribute("role", "alert");
    validationMessage.hidden = true;
    popup.appendChild(validationMessage);

    var actions = document.createElement("div");
    actions.className = "cm-time-picker-actions";
    var cancel = document.createElement("button");
    cancel.type = "button";
    cancel.className = "btn btn-outline-light btn-sm";
    cancel.textContent = "Cancel";
    var apply = document.createElement("button");
    apply.type = "button";
    apply.className = "btn btn-gold btn-sm";
    apply.textContent = "Set time";
    actions.appendChild(cancel);
    actions.appendChild(apply);
    popup.appendChild(actions);
    document.body.appendChild(popup);

    input.setAttribute("aria-haspopup", "dialog");
    input.setAttribute("aria-controls", popup.id);
    input.setAttribute("aria-expanded", "false");

    function currentTime() {
      return parseTime(input.value) || { hour: 12, minute: 0, period: "AM" };
    }

    function updateDisplay() {
      var parsed = parseTime(input.value);
      if (parsed) {
        input.value = formatDisplay(parsed);
      }
    }

    function positionPopup() {
      if (!popup.classList.contains("show")) {
        return;
      }
      var rect = wrapper.getBoundingClientRect();
      var width = Math.min(320, window.innerWidth - 24);
      popup.style.width = width + "px";
      popup.style.left = Math.max(0, Math.min(rect.left, window.innerWidth - width)) + "px";
      popup.style.maxHeight = Math.max(0, window.innerHeight - 24) + "px";
      popup.style.overflowY = "visible";
      var popupHeight = popup.getBoundingClientRect().height;
      var below = window.innerHeight - rect.bottom;
      var above = rect.top;
      var top;
      if (below >= popupHeight + 8) {
        top = rect.bottom + 8;
      } else if (above >= popupHeight + 8) {
        top = rect.top - popupHeight - 8;
      } else {
        top = below >= above ? rect.bottom + 8 : rect.top - popupHeight - 8;
      }
      popup.style.top = Math.max(12, Math.min(top, window.innerHeight - popupHeight - 12)) + "px";
    }

    var suppressFocusOpen = false;

    function closePopup(returnFocus) {
      popup.classList.remove("show");
      popup.querySelectorAll(".cm-time-select-menu.show").forEach(function (menu) {
        menu.classList.remove("show", "open-up");
        menu.previousElementSibling.setAttribute("aria-expanded", "false");
      });
      trigger.setAttribute("aria-expanded", "false");
      input.setAttribute("aria-expanded", "false");
      if (returnFocus) {
        suppressFocusOpen = true;
        input.focus();
        suppressFocusOpen = false;
      }
    }

    function openPopup(focusControl) {
      var selected = currentTime();
      hour.input.value = String(selected.hour).padStart(2, "0");
      minute.input.value = String(selected.minute).padStart(2, "0");
      period.value = selected.period;
      clearTimeValidation();
      popup.classList.add("show");
      trigger.setAttribute("aria-expanded", "true");
      input.setAttribute("aria-expanded", "true");
      positionPopup();
      if (focusControl) {
        hour.input.focus();
      }
    }

    function applyTime() {
      var hourValue = hour.input.value.trim();
      var minuteValue = minute.input.value.trim();
      var parsedHour = /^\d{1,2}$/.test(hourValue) ? Number(hourValue) : NaN;
      var parsedMinute = /^\d{1,2}$/.test(minuteValue) ? Number(minuteValue) : NaN;
      if (!Number.isInteger(parsedHour) || parsedHour < 1 || parsedHour > 12) {
        showTimeValidation("Enter an hour from 1 to 12.", hour.input);
        return;
      }
      if (!Number.isInteger(parsedMinute) || parsedMinute < 0 || parsedMinute > 59) {
        showTimeValidation("Enter minutes from 00 to 59.", minute.input);
        return;
      }
      var selected = {
        hour: parsedHour,
        minute: parsedMinute,
        period: period.value,
      };
      input.value = String(selected.hour).padStart(2, "0") + ":" + String(selected.minute).padStart(2, "0") + " " + selected.period;
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.dispatchEvent(new Event("change", { bubbles: true }));
      closePopup(true);
    }

    function clearTimeValidation() {
      validationMessage.hidden = true;
      validationMessage.textContent = "";
      [hour.input, minute.input].forEach(function (field) {
        field.removeAttribute("aria-invalid");
        field.classList.remove("is-invalid");
      });
    }

    function showTimeValidation(message, field) {
      validationMessage.textContent = message;
      validationMessage.hidden = false;
      [hour.input, minute.input].forEach(function (control) {
        control.removeAttribute("aria-invalid");
        control.classList.remove("is-invalid");
      });
      field.setAttribute("aria-invalid", "true");
      field.classList.add("is-invalid");
      field.focus();
    }

    input.addEventListener("focus", function () {
      if (!suppressFocusOpen) {
        openPopup(false);
      }
    });
    input.addEventListener("click", function () {
      openPopup(false);
    });
    input.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && popup.classList.contains("show")) {
        event.preventDefault();
        closePopup(false);
      }
    });
    input.addEventListener("blur", updateDisplay);
    trigger.addEventListener("click", function () {
      openPopup(true);
    });
    [hour.input, minute.input].forEach(function (field) {
      field.addEventListener("input", function () {
        field.value = field.value.replace(/\D/g, "").slice(0, 2);
        clearTimeValidation();
      });
    });
    apply.addEventListener("click", applyTime);
    cancel.addEventListener("click", function () {
      closePopup(true);
    });
    popup.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        event.preventDefault();
        closePopup(true);
      }
    });
    document.addEventListener("pointerdown", function (event) {
      if (!wrapper.contains(event.target) && !popup.contains(event.target)) {
        closePopup(false);
      }
    });
    window.addEventListener("resize", positionPopup);
    window.addEventListener("scroll", positionPopup, true);
    form.addEventListener("submit", function () {
      var parsed = parseTime(input.value);
      if (parsed) {
        var hour24 = parsed.hour % 12 + (parsed.period === "PM" ? 12 : 0);
        input.value = String(hour24).padStart(2, "0") + ":" + String(parsed.minute).padStart(2, "0");
      }
    });

    updateDisplay();
  });
}

function createTimeInput(label, min, max) {
  var container = document.createElement("div");
  container.className = "cm-time-picker-control";
  var caption = document.createElement("label");
  caption.textContent = label;
  var input = document.createElement("input");
  input.type = "text";
  input.className = "cm-time-picker-number form-control";
  input.inputMode = "numeric";
  input.autocomplete = "off";
  input.maxLength = 2;
  input.setAttribute("aria-label", label);
  input.setAttribute("aria-valuemin", String(min));
  input.setAttribute("aria-valuemax", String(max));
  container.appendChild(caption);
  container.appendChild(input);
  return { container: container, input: input };
}

function createTimeSelect(label, values) {
  var container = document.createElement("div");
  container.className = "cm-time-picker-control";
  var caption = document.createElement("span");
  caption.textContent = label;
  container.appendChild(caption);
  var trigger = document.createElement("button");
  trigger.type = "button";
  trigger.className = "cm-time-select-trigger";
  trigger.setAttribute("aria-label", label);
  trigger.setAttribute("aria-haspopup", "listbox");
  trigger.setAttribute("aria-expanded", "false");
  container.appendChild(trigger);

  var menu = document.createElement("div");
  menu.className = "cm-time-select-menu";
  menu.setAttribute("role", "listbox");
  menu.setAttribute("aria-label", label);
  container.appendChild(menu);

  var options = [];
  var selectedValue = values[0];
  var valueLabel = function (value) {
    return typeof value === "number" ? String(value).padStart(2, "0") : value;
  };
  var selectControl = {
    container: container,
    focus: function () {
      trigger.focus();
    },
    set value(value) {
      selectedValue = typeof values[0] === "number" ? Number(value) : value;
      trigger.textContent = valueLabel(selectedValue);
      options.forEach(function (option) {
        var isSelected = option.value === String(selectedValue);
        option.button.setAttribute("aria-selected", String(isSelected));
        option.button.classList.toggle("selected", isSelected);
      });
    },
    get value() {
      return selectedValue;
    },
  };

  function closeMenu(returnFocus) {
    menu.classList.remove("show", "open-up");
    trigger.setAttribute("aria-expanded", "false");
    if (returnFocus) {
      trigger.focus();
    }
  }

  function positionMenu() {
    menu.classList.remove("open-up");
    var rect = trigger.getBoundingClientRect();
    var availableBelow = window.innerHeight - rect.bottom;
    var availableAbove = rect.top;
    var desiredHeight = Math.min(menu.scrollHeight, 180);
    var openUp = availableBelow < desiredHeight && availableAbove > availableBelow;
    if (openUp) {
      menu.classList.add("open-up");
    }
    menu.style.maxHeight = Math.max(48, Math.min(180, (openUp ? availableAbove : availableBelow) - 12)) + "px";
  }

  function openMenu() {
    document.querySelectorAll(".cm-time-select-menu.show").forEach(function (openMenuElement) {
      if (openMenuElement !== menu) {
        openMenuElement.classList.remove("show", "open-up");
        openMenuElement.previousElementSibling.setAttribute("aria-expanded", "false");
      }
    });
    menu.classList.add("show");
    trigger.setAttribute("aria-expanded", "true");
    positionMenu();
  }

  values.forEach(function (value) {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "cm-time-select-option";
    button.setAttribute("role", "option");
    button.value = String(value);
    button.textContent = valueLabel(value);
    button.addEventListener("click", function () {
      selectControl.value = value;
      closeMenu(true);
    });
    menu.appendChild(button);
    options.push({ value: String(value), button: button });
  });

  trigger.addEventListener("click", function () {
    if (menu.classList.contains("show")) {
      closeMenu(false);
    } else {
      openMenu();
    }
  });
  trigger.addEventListener("keydown", function (event) {
    if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openMenu();
      var selected = options.find(function (option) {
        return option.value === String(selectedValue);
      });
      (selected || options[0]).button.focus();
    }
  });
  menu.addEventListener("keydown", function (event) {
    var currentIndex = options.findIndex(function (option) {
      return option.button === document.activeElement;
    });
    if (event.key === "Escape") {
      event.preventDefault();
      event.stopPropagation();
      closeMenu(true);
    } else if (event.key === "ArrowDown" || event.key === "ArrowUp" || event.key === "Home" || event.key === "End") {
      event.preventDefault();
      var nextIndex = event.key === "Home" ? 0
        : event.key === "End" ? options.length - 1
          : (currentIndex + (event.key === "ArrowDown" ? 1 : -1) + options.length) % options.length;
      options[nextIndex].button.focus();
    }
  });
  window.addEventListener("resize", function () {
    if (menu.classList.contains("show")) {
      positionMenu();
    }
  });
  window.addEventListener("scroll", function () {
    if (menu.classList.contains("show")) {
      positionMenu();
    }
  }, true);

  selectControl.value = selectedValue;
  return selectControl;
}

function parseTime(value) {
  var match = value.trim().match(/^(\d{1,2}):(\d{2})(?::\d{2})?\s*(AM|PM)?$/i);
  if (!match) {
    return null;
  }
  var hour = Number(match[1]);
  var minute = Number(match[2]);
  var period = match[3] ? match[3].toUpperCase() : null;
  if (minute > 59 || (period && (hour < 1 || hour > 12)) || (!period && hour > 23)) {
    return null;
  }
  if (!period) {
    period = hour >= 12 ? "PM" : "AM";
    hour = hour % 12 || 12;
  }
  return { hour: hour, minute: minute, period: period };
}

function formatDisplay(value) {
  return String(value.hour).padStart(2, "0") + ":" + String(value.minute).padStart(2, "0") + " " + value.period;
}
