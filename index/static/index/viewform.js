document.addEventListener("DOMContentLoaded", () => {
    const logoutUrl = document.querySelector("#logout-url")?.dataset?.url;
    const forceLogout = () => {
        if (!logoutUrl) {
            return;
        }
        window.location.replace(logoutUrl);
    };

    const logoutButton = document.querySelector("#logout-button");
    if (logoutButton) {
        logoutButton.addEventListener("click", forceLogout);
    }

    if (window.history.state?.sforViewFormLoaded !== true) {
        window.history.replaceState({sforViewFormLoaded: true}, "", window.location.href);
    }

    window.addEventListener("pageshow", event => {
        if (event.persisted || (window.performance && window.performance.getEntriesByType("navigation")[0]?.type === "back_forward")) {
            forceLogout();
        }
    });

    window.addEventListener("popstate", () => {
        forceLogout();
    });

    document.body.style.backgroundColor =  document.querySelector("#bg-color").innerHTML;
    document.body.style.color =  document.querySelector("#text-color").innerHTML;
    document.querySelectorAll(".txtClr").forEach(element => {
        element.style.color = document.querySelector("#text-color").innerHTML;
    })
    document.querySelectorAll(".textarea-adjust").forEach(tx => {
        tx.style.height = "auto";
        tx.style.height = (10 + tx.scrollHeight)+"px";
        tx.addEventListener('input', e => {
            tx.style.height = "auto";
            tx.style.height = (10 + tx.scrollHeight)+"px";
        })
    })
    document.querySelectorAll('input[type="checkbox"]').forEach(element => {
        document.getElementsByName(element.name).forEach(checkbox => {
            checkbox.addEventListener("input", function(){
                let totalChecked = 0
                document.getElementsByName(element.name).forEach(checkbox => {
                    if(checkbox.checked) totalChecked++;
                })
                if(totalChecked > 0){
                    document.getElementsByName(element.name).forEach(checkbox => {
                        checkbox.removeAttribute("required")
                    })
                }else{
                    document.getElementsByName(element.name).forEach(checkbox => {
                        checkbox.setAttribute("required", '')
                    })
                }
            })
        })
    })

    const rutInput = document.getElementById("rut-input");
    if (rutInput) {
        const validateRUT = (rut) => {
            if (!rut || rut.length < 8) return false;
            let tmp = rut.split('-');
            let digv = tmp[1];
            let rutBody = tmp[0].replace(/\./g, '');
            if (digv === 'K') digv = 'k';
            
            let m = 0, s = 1;
            for (; rutBody; rutBody = Math.floor(rutBody / 10))
                s = (s + rutBody % 10 * (9 - m++ % 6)) % 11;
            let expectedDigit = s ? s - 1 + '' : 'k';
            return expectedDigit === digv;
        };

        rutInput.addEventListener("input", function(e) {
            let value = e.target.value.replace(/\./g, '').replace('-', '');
            
            if (value.match(/^0/)) {
                value = value.replace(/^0+/, '');
            }

            // Max 9 digits for RUT body + DV (8+1 or 7+1)
            if (value.length > 9) {
                value = value.slice(0, 9);
            }
            
            let dv = '';
            if (value.length > 0) {
                dv = value.slice(-1);
                value = value.slice(0, -1);
            }
            
            let formatted = '';
            for (let i = value.length, j = 1; i > 0; i--, j++) {
                formatted = value[i - 1] + formatted;
                if (j % 3 === 0 && i !== 1) {
                    formatted = '.' + formatted;
                }
            }
            
            if (dv !== '') {
                e.target.value = formatted + '-' + dv;
            } else {
                e.target.value = formatted;
            }

            // Validation feedback
            if (e.target.value.length > 0) {
                if (!validateRUT(e.target.value)) {
                    e.target.classList.add("is-invalid");
                    e.target.setCustomValidity("RUT inválido");
                } else {
                    e.target.classList.remove("is-invalid");
                    e.target.setCustomValidity("");
                }
            } else {
                e.target.classList.remove("is-invalid");
                e.target.setCustomValidity("");
            }
        });
        if (rutInput.value) {
            rutInput.dispatchEvent(new Event('input'));
        }
    }
})