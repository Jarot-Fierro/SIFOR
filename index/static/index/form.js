document.addEventListener("DOMContentLoaded", () => {
    const csrf = Cookies.get('csrftoken');
    document.body.style.backgroundColor =  document.querySelector("#bg-color").innerHTML;
    document.body.style.color =  document.querySelector("#text-color").innerHTML;
    document.querySelectorAll(".txt-clr").forEach(element => {
        element.style.color = document.querySelector("#text-color").innerHTML;
    })
    document.querySelectorAll(".input-form-title").forEach(title => {
        title.addEventListener("input", function(){
            fetch(`edit_title`, {
                method: "POST",
                headers: {'X-CSRFToken': csrf},
                body: JSON.stringify({
                    "title": this.value
                })

            })
            document.title = `${this.value} - Google Forms CLONE`
            document.querySelectorAll(".input-form-title").forEach(ele => {
                ele.value = this.value;
            })
        })
    })
    document.querySelector("#input-form-description").addEventListener("input", function(){
        fetch('edit_description', {
            method: "POST",
            headers: {'X-CSRFToken': csrf},
            body: JSON.stringify({
                "description": this.value
            })
        })
    })
    // document.querySelectorAll(".textarea-adjust").forEach(tx => {
    //     tx.style.height = "auto";
    //     tx.style.height = (10 + tx.scrollHeight)+"px";
    //     tx.addEventListener('input', e => {
    //         tx.style.height = "auto";
    //         tx.style.height = (10 + tx.scrollHeight)+"px";
    //     })
    // })
    document.querySelector("#customize-theme-btn").addEventListener('click', () => {
        document.querySelector("#customize-theme").style.display = "block";
        document.querySelector("#close-customize-theme").addEventListener('click', () => {
            document.querySelector("#customize-theme").style.display = "none";
        })
        window.onclick = e => {
            if(e.target == document.querySelector("#customize-theme")) document.querySelector("#customize-theme").style.display = "none";
        }
    })
    document.querySelector("#input-bg-color").addEventListener("input", function(){
        document.body.style.backgroundColor = this.value;
        fetch('edit_background_color', {
            method: "POST",
            headers: {'X-CSRFToken': csrf},
            body: JSON.stringify({
                "bgColor": this.value
            })
        })
    })
    document.querySelector("#input-text-color").addEventListener("input", function(){
        document.querySelectorAll(".txt-clr").forEach(element => {
            element.style.color = this.value;
        })
        fetch('edit_text_color', {
            method: "POST",
            headers: {'X-CSRFToken': csrf},
            body: JSON.stringify({
                "textColor": this.value
            })
        })
    })
    document.querySelectorAll(".open-setting").forEach(ele => {
        ele.addEventListener('click', () => {
            document.querySelector("#setting").style.display = "block";
        })
        document.querySelector("#close-setting").addEventListener('click', () => {
            document.querySelector("#setting").style.display = "none";
        })
        window.onclick = e => {
            if(e.target == document.querySelector("#setting")) document.querySelector("#setting").style.display = "none";
        }
    })
    document.querySelectorAll("#send-form-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelector("#send-form").style.display = "block";
        })
        document.querySelector("#close-send-form").addEventListener("click", () => {
            document.querySelector("#send-form").style.display = "none";
        })
        window.onclick = e => {
            if(e.target == document.querySelector("#send-form")) document.querySelector("#send-form").style.display = "none";
        }
    })
    const copyToClipboard = text => {
        if (navigator.clipboard && window.isSecureContext) {
            return navigator.clipboard.writeText(text);
        }

        return new Promise((resolve, reject) => {
            const tempTextarea = document.createElement("textarea");
            tempTextarea.value = text;
            tempTextarea.style.position = "fixed";
            tempTextarea.style.left = "-9999px";
            tempTextarea.style.top = "0";
            document.body.appendChild(tempTextarea);
            tempTextarea.focus();
            tempTextarea.select();

            try {
                const copied = document.execCommand("copy");
                document.body.removeChild(tempTextarea);
                if (copied) {
                    resolve();
                    return;
                }
                reject(new Error("No se pudo copiar el enlace."));
            } catch (error) {
                document.body.removeChild(tempTextarea);
                reject(error);
            }
        });
    };

    document.querySelectorAll("[copy-btn]").forEach(btn => {
        btn.addEventListener("click", event => {
            event.preventDefault();
            const url = document.getElementById("copy-url");
            if (!url) return;

            copyToClipboard(url.value)
                .then(() => {
                    document.querySelector("#send-form").style.display = "none";
                })
                .catch(() => {
                    alert("No fue posible copiar el enlace. Intenta nuevamente.");
                });
        })
    })
    const establecimientosSelect = document.querySelector("#establecimientos-select");
    const selectedEstablecimientos = document.querySelector("#selected-establecimientos");
    const establecimientosWarning = document.querySelector("#establecimientos-warning");
    const establecimientosSettings = document.querySelector("#establecimientos-settings");

    const getSelectedEstablecimientos = () => {
        if (!establecimientosSelect) return [];
        return [...establecimientosSelect.selectedOptions].map(option => Number(option.value));
    }

    const renderSelectedEstablecimientos = () => {
        if (!establecimientosSelect || !selectedEstablecimientos || !establecimientosWarning) return;
        const selectedOptions = [...establecimientosSelect.selectedOptions];
        selectedEstablecimientos.innerHTML = "";

        if (selectedOptions.length === 0) {
            establecimientosWarning.style.display = "block";
            const emptyState = document.createElement("p");
            emptyState.classList.add("small", "mb-0", "text-muted");
            emptyState.innerText = "No hay establecimientos seleccionados.";
            selectedEstablecimientos.appendChild(emptyState);
            return;
        }

        establecimientosWarning.style.display = "none";
        selectedOptions.forEach(option => {
            const badge = document.createElement("span");
            badge.classList.add("badge", "bg-primary", "me-2", "mb-2");
            badge.innerText = option.text;
            selectedEstablecimientos.appendChild(badge);
        })
    }

    if (establecimientosSelect) {
        const selectedFromData = establecimientosSettings ? JSON.parse(establecimientosSettings.dataset.selected || "[]") : [];
        if (selectedFromData.length > 0) {
            const selectedIds = selectedFromData.map(item => String(item.id));
            [...establecimientosSelect.options].forEach(option => {
                option.selected = selectedIds.includes(option.value);
            })
        }
        renderSelectedEstablecimientos();
        establecimientosSelect.addEventListener("change", renderSelectedEstablecimientos);
    }

    document.querySelector("#setting-form").addEventListener("submit", e => {
        e.preventDefault();
        const isQuizElement = document.querySelector("#is_quiz");
        const authenticatedResponderElement = document.querySelector("#authenticated_responder");
        fetch('edit_setting', {
            method: "POST",
            headers: {'X-CSRFToken': csrf},
            body: JSON.stringify({
                "collect_email": document.querySelector("#collect_email").checked,
                "is_quiz": isQuizElement ? isQuizElement.checked : false,
                "is_public": document.querySelector("#is_public").checked,
                "authenticated_responder": authenticatedResponderElement ? authenticatedResponderElement.checked : false,
                "confirmation_message": document.querySelector("#comfirmation_message").value,
                "edit_after_submit": document.querySelector("#edit_after_submit").checked,
                "allow_view_score": document.querySelector("#allow_view_score").checked,
                "establecimientos": getSelectedEstablecimientos(),
            })
        })
        document.querySelector("#setting").style.display = "none";
        if(!document.querySelector("#collect_email").checked){
            if(document.querySelector(".collect-email")) document.querySelector(".collect-email").parentNode.removeChild(document.querySelector(".collect-email"))
        }else{
            if(!document.querySelector(".collect-email")){
                let collect_email = document.createElement("div");
                collect_email.classList.add("collect-email", "txt-clr", "alert", "alert-light", "mt-3", "mb-0", "border")
                collect_email.innerHTML = `<h3 class="question-title h5">Email address <span class="require-star text-danger">*</span></h3>
                <input type="text" autoComplete="off" aria-label="Valid email address" disabled dir = "auto" class="require-email-edit form-control"
                placeholder = "Valid email address" />
                <p class="collect-email-desc mb-0 mt-2 small">This form is collecting email addresses. <span class="open-setting text-primary" role="button">Change settings</span></p>`
                document.querySelector("#form-head").appendChild(collect_email)
            }
        }
        if(isQuizElement && isQuizElement.checked){
            if(!document.querySelector("#add-score")){
                let is_quiz = document.createElement('a')
                is_quiz.setAttribute("href", "score");
                is_quiz.setAttribute("id", "add-score");
                is_quiz.innerHTML = `<img src = "/static/Icon/score.png" id="add-score" class = "form-option-icon" title = "Add score" alt = "Score icon" />`;
                document.querySelector(".question-options").appendChild(is_quiz)
            }
            if(!document.querySelector(".score")){
                let quiz_nav = document.createElement("span");
                quiz_nav.classList.add("col-4");
                quiz_nav.classList.add("navigation");
                quiz_nav.classList.add('score');
                quiz_nav.innerHTML =   `<a href = "score" class="link">Scores</a>`;
                [...document.querySelector(".form-navigation").children].forEach(element => {
                    element.classList.remove("col-6")
                    element.classList.add('col-4')
                })
                document.querySelector(".form-navigation").insertBefore(quiz_nav, document.querySelector(".form-navigation").childNodes[2])
            }
        }else{
            if(document.querySelector("#add-score")) document.querySelector("#add-score").parentNode.removeChild(document.querySelector("#add-score"))
            if(document.querySelector(".score")){
                [...document.querySelector(".form-navigation").children].forEach(element => {
                    element.classList.remove("col-4")
                    element.classList.add('col-6')
                })
                document.querySelector(".score").parentNode.removeChild(document.querySelector(".score"))
            }
        }
    })
    document.querySelector("#delete-form").addEventListener("submit", e => {
        e.preventDefault();
        if(window.confirm("Estas seguro que quieres ELIMINAR todas las respuestas? Esta accion NO se puede deshacer")){
            fetch('delete', {
                method: "DELETE",
                headers: {'X-CSRFToken': csrf}
            })
            .then(() => window.location = `${window.APP_URL_PREFIX}/`)
        }
    })
    const editQuestion = () => {
        document.querySelectorAll(".input-question").forEach(question => {
            question.addEventListener('input', function(){
                let question_type;
                let required;
                document.querySelectorAll(".input-question-type").forEach(qp => {
                    if(qp.dataset.id === this.dataset.id) question_type = qp.value
                })
                document.querySelectorAll('.required-checkbox').forEach(rc => {
                    if(rc.dataset.id === this.dataset.id) required = rc.checked;
                })
                fetch('edit_question', {
                    method: "POST",
                    headers: {'X-CSRFToken': csrf},
                    body: JSON.stringify({
                        id: this.dataset.id,
                        question: this.value,
                        question_type: question_type,
                        required: required
                    })
                })
            })
        })
    }
    editQuestion();
    
    const editRequire = () => {
        document.querySelectorAll(".required-checkbox").forEach(checkbox => {
            checkbox.addEventListener('input', function(){
                let question;
                let question_type;
                document.querySelectorAll(".input-question-type").forEach(qp => {
                    if(qp.dataset.id === this.dataset.id) question_type = qp.value
                })
                document.querySelectorAll('.input-question').forEach(q => {
                    if(q.dataset.id === this.dataset.id) question = q.value
                })
                fetch('edit_question', {
                    method: "POST",
                    headers: {'X-CSRFToken': csrf},
                    body: JSON.stringify({
                        id: this.dataset.id,
                        question: question,
                        question_type: question_type,
                        required: this.checked
                    })
                })
            })
        })
    }
    editRequire()
    const editChoice = () => {
        document.querySelectorAll(".edit-choice").forEach(choice => {
            choice.addEventListener("input", function(){
                fetch('edit_choice', {
                    method: "POST",
                    headers: {'X-CSRFToken': csrf},
                    body: JSON.stringify({
                        "id": this.dataset.id,
                        "choice": this.value
                    })
                })
            })
        })
    }
    editChoice()
    const removeOption = () => {
        document.querySelectorAll(".remove-option").forEach(ele => {
            ele.addEventListener("click",function(){
                fetch('remove_choice', {
                    method: "POST",
                    headers: {'X-CSRFToken': csrf},
                    body: JSON.stringify({
                        "id": this.dataset.id
                    })
                })
                .then(() => {
                    this.parentNode.parentNode.removeChild(this.parentNode)
                })
            })
        })
    }
    removeOption()
    const addOption = () => {
        document.querySelectorAll(".add-option").forEach(question =>{
            question.addEventListener("click", function(){
                fetch('add_choice', {
                    method: "POST",
                    headers: {'X-CSRFToken': csrf},
                    body: JSON.stringify({
                        "question": this.dataset.question
                    })
                })
                .then(response => response.json())
                .then(result => {
                    let element = document.createElement("div");
                    element.classList.add('choice', 'd-flex', 'align-items-center', 'gap-2', 'mb-2');
                    if(this.dataset.type === "multiple choice"){
                        element.innerHTML = `<input type="radio" id="${result["id"]}" disabled>
                        <label for="${result["id"]}">
                            <input type="text" value="${result["choice"]}" class="edit-choice form-control" data-id="${result["id"]}">
                        </label>
                        <span class="remove-option text-danger fs-4 lh-1" title = "Remove" data-id="${result["id"]}">&times;</span>`;
                    }else if(this.dataset.type === "checkbox"){
                        element.innerHTML = `<input type="checkbox" id="${result["id"]}" disabled>
                        <label for="${result["id"]}">
                            <input type="text" value="${result["choice"]}" class="edit-choice form-control" data-id="${result["id"]}">
                        </label>
                        <span class="remove-option text-danger fs-4 lh-1" title = "Remove" data-id="${result["id"]}">&times;</span>`;
                    }
                    document.querySelectorAll(".choices").forEach(choices => {
                        if(choices.dataset.id === this.dataset.question){
                            choices.insertBefore(element, choices.childNodes[choices.childNodes.length -2]);
                            editChoice()
                            removeOption()
                        }
                    });
                })
            })
        })
    }
    addOption()
    const deleteQuestion = () => {
        document.querySelectorAll(".delete-question").forEach(question => {
            question.addEventListener("click", function(){
                fetch(`delete_question/${this.dataset.id}`, {
                    method: "DELETE",
                    headers: {'X-CSRFToken': csrf},
                })
                .then(() => {
                    document.querySelectorAll(".question").forEach(q =>{
                        if(q.dataset.id === this.dataset.id){
                            q.parentNode.removeChild(q)
                        }
                    })
                })
            })
        })
    }
    deleteQuestion()
    const changeType = () => {
        document.querySelectorAll(".input-question-type").forEach(ele => {
            ele.addEventListener('input', function(){
                let required;
                let question;
                document.querySelectorAll('.required-checkbox').forEach(rc => {
                    if(rc.dataset.id === this.dataset.id) required = rc.checked;
                })
                document.querySelectorAll('.input-question').forEach(q => {
                    if(q.dataset.id === this.dataset.id) question = q.value
                })
                fetch('edit_question', {
                    method: "POST",
                    headers: {'X-CSRFToken': csrf},
                    body: JSON.stringify({
                        id: this.dataset.id,
                        question: question,
                        question_type: this.value,
                        required: required
                    })
                })

                if(this.dataset.origin_type === "multiple choice" || this.dataset.origin_type === "checkbox"){
                    document.querySelectorAll(".choices").forEach(choicesElement => {
                        if(choicesElement.dataset.id === this.dataset.id){
                            if(this.value === "multiple choice" || this.value === "checkbox"){
                                fetch(`get_choice/${this.dataset.id}`, {
                                    method: "GET"
                                })
                                .then(response => response.json())
                                .then(result => {
                                    let ele = document.createElement("div");
                                    ele.classList.add('choices');
                                    ele.setAttribute("data-id", result["question_id"])
                                    let choices = '';
                                    if(this.value === "multiple choice"){
                                        for(let i in result["choices"]){
                                            if(i){ choices += `<div class="choice d-flex align-items-center gap-2 mb-2">
                                            <input type="radio" id="${result["choices"][i].id}" disabled>
                                            <label for="${result["choices"][i].id}">
                                                <input type="text" data-id="${result["choices"][i].id}" class="edit-choice form-control" value="${result["choices"][i].choice}">
                                            </label>
                                            <span class="remove-option text-danger fs-4 lh-1" title="Remove" data-id="${result["choices"][i].id}">&times;</span></div>`}
                                        }
                                    }else if(this.value === "checkbox"){
                                        for(let i in result["choices"]){
                                            if(i){choices += `<div class="choice d-flex align-items-center gap-2 mb-2">
                                            <input type="checkbox" id="${result["choices"][i].id}" disabled>
                                            <label for="${result["choices"][i].id}">
                                                <input type="text" data-id="${result["choices"][i].id}" class="edit-choice form-control" value="${result["choices"][i].choice}">
                                            </label>
                                            <span class="remove-option text-danger fs-4 lh-1" title="Remove" data-id="${result["choices"][i].id}">&times;</span></div>`}
                                        }
                                    }
                                    ele.innerHTML = `${choices}
                                    <div class="choice d-flex align-items-center gap-2">
                                        <input type = "${this.value === "checkbox" ? "checkbox" : "radio"}" id = "add-choice" disabled />
                                        <label for = "add-choice" class="add-option text-primary" id="add-option" data-question="${result["question_id"]}"
                                        data-type = "${this.value}">Agregar opción</label>
                                    </div>`;
                                    choicesElement.parentNode.replaceChild(ele, choicesElement);
                                    editChoice()
                                    removeOption()
                                    changeType()
                                    editQuestion()
                                    editRequire()
                                    addOption()
                                    deleteQuestion()
                                })
                            }else{
                                if(this.value === "short"){
                                    choicesElement.parentNode.removeChild(choicesElement)
                                    let ele = document.createElement("div");
                                    ele.innerHTML = `<div class="answers" data-id="${this.dataset.id}">
                                    <input type ="text" class="short-answer form-control" disabled placeholder="Escribe texto corto" />
                                </div>`
                                    this.parentNode.insertBefore(ele, this.parentNode.childNodes[4])
                                }else if(this.value === "paragraph"){
                                    choicesElement.parentNode.removeChild(choicesElement)
                                    let ele = document.createElement("div");
                                    ele.innerHTML = `<div class="answers" data-id="${this.dataset.id}">
                                    <textarea class="long-answer form-control" disabled placeholder="Escribe texto largo" ></textarea>
                                </div>`
                                    this.parentNode.insertBefore(ele, this.parentNode.childNodes[4])
                                }
                            }
                        }
                    })
                }else{
                    document.querySelectorAll(".question-box").forEach(question => {
                        document.querySelectorAll(".answers").forEach(answer => {
                            if(answer.dataset.id === this.dataset.id){
                                answer.parentNode.removeChild(answer)
                            }
                        })
                        if((this.value === "multiple choice" || this.value === "checkbox") && question.dataset.id === this.dataset.id){
                            fetch(`get_choice/${this.dataset.id}`, {
                                method: "GET"
                            })
                            .then(response => response.json())
                            .then(result => {
                                let ele = document.createElement("div");
                                ele.classList.add('choices');
                                ele.setAttribute("data-id", result["question_id"])
                                let choices = '';
                                if(this.value === "multiple choice"){
                                    for(let i in result["choices"]){
                                        if(i){ choices += `<div class="choice d-flex align-items-center gap-2 mb-2">
                                        <input type="radio" id="${result["choices"][i].id}" disabled>
                                        <label for="${result["choices"][i].id}">
                                            <input type="text" data-id="${result["choices"][i].id}" class="edit-choice form-control" value="${result["choices"][i].choice}">
                                        </label>
                                        <span class="remove-option text-danger fs-4 lh-1" title="Remove" data-id="${result["choices"][i].id}">&times;</span></div>`}
                                    }
                                }else if(this.value === "checkbox"){
                                    for(let i in result["choices"]){
                                        if(i){choices += `<div class="choice d-flex align-items-center gap-2 mb-2">
                                        <input type="checkbox" id="${result["choices"][i].id}" disabled>
                                        <label for="${result["choices"][i].id}">
                                            <input type="text" data-id="${result["choices"][i].id}" class="edit-choice form-control" value="${result["choices"][i].choice}">
                                        </label>
                                        <span class="remove-option text-danger fs-4 lh-1" title="Remove" data-id="${result["choices"][i].id}">&times;</span></div>`}
                                    }
                                }
                                ele.innerHTML = `${choices}
                                <div class="choice d-flex align-items-center gap-2">
                                    <input type = "${this.value === "checkbox" ? "checkbox" : "radio"}" id = "add-choice" disabled />
                                    <label for = "add-choice" class="add-option text-primary" id="add-option" data-question="${result["question_id"]}"
                                    data-type = "${this.value}">Agregar opción</label>
                                </div>`;
                                question.insertBefore(ele, question.childNodes[4])
                                editChoice()
                                removeOption()
                                changeType()
                                editQuestion()
                                editRequire()
                                addOption()
                                deleteQuestion()
                            })
                        }else{
                            if(this.value === "short"){
                                let ele = document.createElement("div");
                                ele.innerHTML = `<div class="answers" data-id="${this.dataset.id}">
                                <input type ="text" class="short-answer form-control" disabled placeholder="Escribe texto corto" />
                            </div>`
                                this.parentNode.insertBefore(ele, this.parentNode.childNodes[4])
                            }else if(this.value === "paragraph"){
                                let ele = document.createElement("div");
                                ele.innerHTML = `<div class="answers" data-id="${this.dataset.id}">
                                <textarea class="long-answer form-control" disabled placeholder="Escribe texto largo" ></textarea>
                            </div>`
                                this.parentNode.insertBefore(ele, this.parentNode.childNodes[4])
                            }
                        }
                    })
                }
                this.setAttribute("data-origin_type", this.value);
            })
        })
    }
    changeType()
    document.querySelector("#add-question").addEventListener("click", () => {
        fetch('add_question', {
            method: "POST",
            headers: {'X-CSRFToken': csrf},
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(result => {
            let ele = document.createElement('div')
            ele.classList.add('margin-top-bottom', 'box', 'question-box', 'question', 'card', 'border-0', 'shadow-sm', 'rounded-4', 'p-4', 'mb-4');
            ele.setAttribute("data-id", result["question"].id)
            ele.innerHTML = `
            <input type="text" data-id="${result["question"].id}" class="question-title edit-on-click input-question form-control form-control-lg mb-3" value="${result["question"].question}">
            <select class="question-type-select input-question-type form-select mb-3" data-id="${result["question"].id}" data-origin_type = "${result["question"].question_type}">
                <option value="short">Texto Corto</option>
                <option value="paragraph">Parrafo</option>
                <option value="multiple choice" selected>Opciones</option>
                <option value="checkbox">Checkbox</option>
            </select>
            <div class="choices" data-id="${result["question"].id}">
                <div class="choice d-flex align-items-center gap-2 mb-2">
                    <input type="radio" id="${result["choices"].id}" disabled>
                    <label for="${result["choices"].id}">
                        <input type="text" value="${result["choices"].choice}" class="edit-choice form-control" data-id="${result["choices"].id}">
                    </label>
                    <span class="remove-option text-danger fs-4 lh-1" title = "Remove" data-id="${result["choices"].id}">&times;</span>
                </div>
                <div class="choice d-flex align-items-center gap-2">
                    <input type = "radio" id = "add-choice" disabled />
                    <label for = "add-choice" class="add-option text-primary" id="add-option" data-question="${result["question"].id}" 
                    data-type = "${result["question"].question_type}">Agregar opción</label>
                </div>
            </div>
            <div class="choice-option d-flex align-items-center justify-content-between mt-3 pt-3 border-top">
                <div class="form-check m-0">
                    <input type="checkbox" class="required-checkbox form-check-input" id="required-${result["question"].id}" data-id="${result["question"].id}">
                    <label for="required-${result["question"].id}" class="required form-check-label">Requerido</label>
                </div>
                <div>
                    <img src="/static/Icon/dustbin.png" alt="Delete question icon" class="question-option-icon delete-question" title="Delete question"
                    data-id="${result["question"].id}">
                </div>
            </div>
            `;
            document.querySelector(".container").appendChild(ele);
            editChoice()
            removeOption()
            changeType()
            editQuestion()
            editRequire()
            addOption()
            deleteQuestion()
        })
    })
})