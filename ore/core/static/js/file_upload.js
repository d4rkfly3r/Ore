(function($) {
	// bodge to work around the inner container needing to be the same width
	// as the outer container
	var fixProgressBarContainer = function() {
		$(".progress-bar-container").each(function(n, el) {
			var $el = $(el);
			$el.css('width', $el.parents(".progress").outerWidth() + 'px');
		});
	};
	var debouncer = function(fn) {
		var debounceTimer = null;
		return function() {
			if (debounceTimer) {
				clearTimeout(debounceTimer);
				debounceTimer = null;
			}

			debounceTimer = setTimeout(function() {
				debounceTimer = null;
				fn();
			}, 500);
		};
	};
	$(window).resize(debouncer(fixProgressBarContainer));
	$(window).load(fixProgressBarContainer);

	$(window).load(function() {
		var templateEl = document.querySelector("#upload-file-template");
		var fileListEl = document.querySelector(".upload-file-files");
		var dragAreaEl = document.querySelector(".upload-file.area");
		var dragAreaFileEl = document.querySelector("#upload-file-file");

		dragAreaEl.addEventListener('dragenter', function(e) {
			e.stopPropagation();
			e.preventDefault();
		});
		dragAreaEl.addEventListener('dragover', function(e) {
			e.stopPropagation();
			e.preventDefault();
		});
		dragAreaEl.addEventListener('drop', function(e) {
			e.stopPropagation();
			e.preventDefault();

			beginFilesUpload(e.dataTransfer.files);
		});
		dragAreaEl.addEventListener('click', function(e) {
			dragAreaFileEl.click();

			e.preventDefault();
		});

		dragAreaFileEl.addEventListener('change', function(e) {
			beginFilesUpload(dragAreaFileEl.files);

			dragAreaFileEl.parentNode.reset();
		});

		var beginFileUpload = function(file) {
			var status = {
				cancellable: true,
				complete: false,
				success: false,
				error: false,
				aborted: false,
				nodeRemoved: false,
				hiddenNodeExists: false,
			};

			console.log(file.name, "beginning upload");
			var fileEl = templateEl.cloneNode(true);
			fileEl.removeAttribute("id");
			var $fileEl = $(fileEl);
			$fileEl.find(".file-overlay").text(file.name);
			fileEl.classList.remove("hidden");
			fileListEl.appendChild(fileEl);

			var progressBarEl = fileEl.querySelector(".progress-bar");
			var targetFormEl = document.querySelector("#create-version-form");
			var hiddenNodeEl = null;

			var xhr = new XMLHttpRequest();

			xhr.open("POST", "file/", true);
			var progressEv = function(e) {
				if (e.lengthComputable) {
					var percentComplete = e.loaded * 100 / e.total;
					progressBarEl.setAttribute("aria-valuenow", percentComplete);
					progressBarEl.style.width = percentComplete + '%';
				} else {
					progressBarEl.style.width = "100%";
					progressBarEl.classList.add("progress-bar-striped");
					progressBarEl.classList.add("active");
				}
			};
			xhr.upload.onprogress = progressEv;
			xhr.addEventListener("progress", progressEv, false);
			xhr.addEventListener("loadend", function(e) {
				progressBarEl.classList.remove("progress-bar-striped");
				progressBarEl.classList.remove("active");
				progressBarEl.classList.remove("progress-bar-info");
				status.complete = true;
				status.cancellable = false;
			}, false);
			xhr.addEventListener("load", function(e) {
				progressBarEl.setAttribute("aria-valuenow", 100);
				progressBarEl.style.width = '100%';
				if (xhr.status === 200) {
					progressBarEl.classList.add("progress-bar-success");
					status.success = true;

					var j = JSON.parse(xhr.responseText);

					hiddenNodeEl = document.createElement('input');
					hiddenNodeEl.type = "hidden";
					hiddenNodeEl.name = "file";
					hiddenNodeEl.value = j.file_id;
					targetFormEl.appendChild(hiddenNodeEl);


					status.hiddenNodeExists = true;
				} else {
					progressBarEl.classList.add("progress-bar-danger");
					status.error = true;
				}

				console.log(xhr.responseText);
			}, false);
			xhr.addEventListener("abort", function(e) {
				progressBarEl.classList.add("progress-bar-danger");
				status.aborted = true;
				if (!status.nodeRemoved) {
					fileEl.parentNode.removeChild(fileEl);
					status.nodeRemoved = true;
				}
			}, false);
			xhr.addEventListener("error", function(e) {
				progressBarEl.classList.add("progress-bar-danger");
				status.error = true;
			}, false);

			Array.prototype.forEach.call(fileEl.querySelectorAll('.file-remove-button'), function(x) {
				x.addEventListener('click', function() {
					if (!status.nodeRemoved) {
						fileEl.parentNode.removeChild(fileEl);
						status.nodeRemoved = true;
					}

					if (status.complete) {
						console.log("TODO: add some method of removing from list to submit");
					}

					if (status.cancellable) {
						xhr.abort();
					}

					if (status.hiddenNodeExists) {
						hiddenNodeEl.parentNode.removeChild(hiddenNodeEl);
						hiddenNodeEl = null;
						status.hiddenNodeExists = false;
					}

					status.complete = true;
					status.cancellable = false;
					status.aborted = true;
				});
			});

			xhr.setRequestHeader('X-CSRFToken', document.getElementsByName("csrfmiddlewaretoken")[0].value);

			var fd = new FormData();
			fd.append('file', file);
			xhr.send(fd);
		};

		var beginFilesUpload = function(files) {
			Array.prototype.forEach.call(files, beginFileUpload);
			fixProgressBarContainer();
		};
	});
})(jQuery);