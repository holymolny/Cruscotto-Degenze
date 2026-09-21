/* -----------------------------------------------------------------------
   Cruscotto Degenze — comportamenti della pagina.

   Tre regole che valgono per tutto questo file:

   1. Niente librerie esterne. Il programma deve funzionare in reparto anche
      senza internet, e ogni libreria in più è codice di qualcun altro da
      tenere aggiornato per anni.

   2. Niente onclick dentro l'HTML. La Content-Security-Policy consente solo
      codice servito da noi: un onclick scritto nella pagina verrebbe
      bloccato dal browser. Gli agganci si fanno qui, leggendo gli attributi
      data-*.

   3. Il JavaScript è una comodità, non una difesa. Ogni cosa che si fa da
      qui viene comunque ricontrollata dal server: nascondere un pulsante
      non impedisce niente a chi conosce l'indirizzo.
   ----------------------------------------------------------------------- */

(function () {
  "use strict";

  /* ------------------------------------------------------------------
     FINESTRE
     ------------------------------------------------------------------ */
  function apri(idFinestra) {
    var finestra = document.getElementById(idFinestra);
    if (!finestra) return;
    finestra.classList.add("aperto");

    // Il primo campo utile riceve il cursore: in reparto si lavora molto da
    // tastiera e non doverla lasciare per il mouse fa risparmiare tempo.
    var primo = finestra.querySelector("input:not([type=hidden]), select");
    if (primo) primo.focus();
  }

  function chiudiTutte() {
    document.querySelectorAll("[data-finestra].aperto").forEach(function (finestra) {
      finestra.classList.remove("aperto");
    });
  }

  // Il tasto Esc chiude, come ci si aspetta da qualunque finestra.
  document.addEventListener("keydown", function (evento) {
    if (evento.key === "Escape") chiudiTutte();
  });

  // Un clic sullo sfondo scuro chiude. Il controllo su target evita che si
  // chiuda anche cliccando dentro la finestra, i cui clic "risalgono" fin qui.
  document.addEventListener("click", function (evento) {
    if (evento.target.matches("[data-finestra]")) chiudiTutte();
  });

  /* ------------------------------------------------------------------
     TOKEN CSRF
     ------------------------------------------------------------------ */
  function tokenCsrf() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
  }

  /* ------------------------------------------------------------------
     AZIONI
     ------------------------------------------------------------------ */
  var azioni = {
    "chiudi": chiudiTutte,

    "apri-aiuto": function () {
      // La finestra d'aiuto della pagina di accesso: solo testo, niente da preparare.
      apri("velo-aiuto");
    },

    "apri-nuovo": function (bottone) {
      var modulo = document.querySelector("#velo-nuovo form");
      modulo.querySelector('[name="reparto_id"]').value = bottone.dataset.reparto;
      document.getElementById("nuovo-reparto-nome").textContent =
        "Reparto: " + bottone.dataset.repartoNome;
      apri("velo-nuovo");
    },

    "apri-dimissione": function (bottone) {
      var modulo = document.getElementById("form-dimissione");
      modulo.action = "/paziente/" + bottone.dataset.paziente + "/dimissione";
      document.getElementById("dimissione-nome").textContent = bottone.dataset.nome;

      var campo = document.getElementById("dimissione-data");
      campo.value = bottone.dataset.data || "";
      // min impedisce al browser di proporre una data precedente all'arrivo.
      // Il controllo vero lo rifà il server: questo serve solo a evitare
      // all'utente di scoprire l'errore dopo aver premuto Salva.
      campo.min = bottone.dataset.arrivo || "";
      apri("velo-dimissione");
    },

    "apri-sposta": function (bottone) {
      var modulo = document.getElementById("form-sposta");
      modulo.action = "/paziente/" + bottone.dataset.paziente + "/sposta";
      document.getElementById("sposta-nome").textContent =
        bottone.dataset.nome + " — attualmente al letto " + bottone.dataset.letto;
      document.getElementById("sposta-reparto").value = bottone.dataset.reparto;
      document.getElementById("sposta-letto").value = bottone.dataset.letto;
      apri("velo-sposta");
    },

    "apri-elimina": function (bottone) {
      var modulo = document.getElementById("form-elimina");
      modulo.action = "/paziente/" + bottone.dataset.paziente + "/elimina";
      document.getElementById("elimina-nome").textContent =
        bottone.dataset.nome + " — letto " + bottone.dataset.letto;
      apri("velo-elimina");
    },

    "gravita": function (bottone) {
      cambiaGravita(bottone);
    },

    /* ---- Gestione utenti ---- */

    "apri-nuovo-utente": function () {
      // Nessun dato da precaricare: il form nasce vuoto.
      apri("velo-nuovo-utente");
    },

    "apri-modifica-utente": function (bottone) {
      var modulo = document.getElementById("form-modifica-utente");
      modulo.action = "/utenti/" + bottone.dataset.utente + "/modifica";
      document.getElementById("modifica-utente-nome").textContent =
        bottone.dataset.etichetta;

      document.getElementById("modifica-utente-campo-nome").value = bottone.dataset.nome;
      document.getElementById("modifica-utente-campo-cognome").value = bottone.dataset.cognome;
      document.getElementById("modifica-utente-campo-ruolo").value = bottone.dataset.ruolo;
      apri("velo-modifica-utente");
    },

    "apri-password-utente": function (bottone) {
      var modulo = document.getElementById("form-password-utente");
      modulo.action = "/utenti/" + bottone.dataset.utente + "/password";
      document.getElementById("password-utente-nome").textContent =
        bottone.dataset.etichetta;

      // Svuotato a ogni apertura: senza, riaprendo la finestra per un'altra
      // persona si troverebbe dentro la password digitata per la precedente.
      modulo.reset();
      apri("velo-password-utente");
    },

    "apri-disattiva-utente": function (bottone) {
      var modulo = document.getElementById("form-disattiva-utente");
      modulo.action = "/utenti/" + bottone.dataset.utente + "/disattiva";
      document.getElementById("disattiva-utente-nome").textContent =
        bottone.dataset.etichetta;
      apri("velo-disattiva-utente");
    },

    "apri-agenda": function (bottone) {
      pazienteAperto = bottone.dataset.paziente;
      document.getElementById("agenda-titolo").textContent = bottone.dataset.nome;
      document.getElementById("agenda-sotto").textContent = bottone.dataset.sotto;

      var scarica = document.getElementById("agenda-pdf");
      if (scarica) scarica.href = "/paziente/" + pazienteAperto + "/pdf";

      document.getElementById("agenda-corpo").innerHTML =
        '<p class="vuoto-agenda">Caricamento…</p>';
      apri("velo-agenda");
      caricaAgenda("/paziente/" + pazienteAperto + "/agenda", { method: "GET" });
    },

    "modifica-nota": function (bottone) {
      mostraPannelloNota(bottone.dataset.nota, "modifica");
    },

    "annulla-modifica": function (bottone) {
      nascondiPannelliNota(bottone.dataset.nota);
    },

    "elimina-nota": function (bottone) {
      mostraPannelloNota(bottone.dataset.nota, "conferma");
    },

    "annulla-elimina": function (bottone) {
      nascondiPannelliNota(bottone.dataset.nota);
    }
  };

  /* Un solo ascoltatore per tutta la pagina, invece di uno per pulsante.
     Si chiama "delega": il clic risale fino a document, e qui si guarda da
     quale pulsante è partito. Funziona anche per i pulsanti che non
     esistevano al caricamento della pagina. */
  document.addEventListener("click", function (evento) {
    var bottone = evento.target.closest("[data-azione]");
    if (!bottone || bottone.disabled) return;

    var azione = azioni[bottone.dataset.azione];
    if (!azione) return;

    evento.preventDefault();
    azione(bottone);
  });

  /* ------------------------------------------------------------------
     GRAVITÀ: salvataggio immediato
     ------------------------------------------------------------------ */
  function cambiaGravita(bottone) {
    // Disabilitato durante l'attesa: due clic rapidi farebbero avanzare il
    // ciclo due volte, e l'utente vedrebbe un colore che non ha scelto.
    if (bottone.dataset.inCorso === "si") return;
    bottone.dataset.inCorso = "si";

    fetch("/paziente/" + bottone.dataset.paziente + "/gravita", {
      method: "POST",
      headers: {
        "X-CSRFToken": tokenCsrf(),
        "Accept": "application/json"
      },
      // Senza questo il browser non allega il cookie di sessione e il server
      // ci considererebbe non collegati.
      credentials: "same-origin"
    })
      .then(function (risposta) {
        if (!risposta.ok) throw new Error("risposta " + risposta.status);
        return risposta.json();
      })
      .then(function (dati) {
        bottone.dataset.g = dati.gravita;
        bottone.title = dati.etichetta;
        bottone.setAttribute("aria-label", "Gravità: " + dati.etichetta);
      })
      .catch(function () {
        avvisa("Non è stato possibile salvare la gravità. Ricarica la pagina.");
      })
      .finally(function () {
        bottone.dataset.inCorso = "no";
      });
  }

  /* ------------------------------------------------------------------
     AGENDA

     Il contenuto della finestra lo disegna il server e arriva già pronto:
     qui lo si infila nella pagina e basta. Costruirlo in JavaScript
     vorrebbe dire incollare a mano il testo scritto dagli utenti dentro
     dell'HTML, e sarebbe sufficiente una dimenticanza per trasformare una
     nota in codice eseguibile.
     ------------------------------------------------------------------ */
  var pazienteAperto = null;

  function caricaAgenda(indirizzo, opzioni) {
    opzioni = opzioni || {};

    var richiesta = {
      method: opzioni.method || "GET",
      credentials: "same-origin",
      // Non impostiamo Content-Type: con un FormData ci pensa il browser,
      // che deve anche calcolarsi il separatore fra i campi.
      headers: { "X-CSRFToken": tokenCsrf(), "Accept": "application/json" }
    };
    if (opzioni.body) richiesta.body = opzioni.body;

    return fetch(indirizzo, richiesta)
      .then(function (risposta) {
        if (!risposta.ok) throw new Error("risposta " + risposta.status);
        return risposta.json();
      })
      .then(function (dati) {
        document.getElementById("agenda-corpo").innerHTML = dati.html;
        aggiornaContatoreNote(dati.paziente, dati.note);
        ripristinaStatoChecklist();
      })
      .catch(function () {
        avvisa("Non è stato possibile aprire l'Agenda. Ricarica la pagina.");
      });
  }

  function aggiornaContatoreNote(pazienteId, quante) {
    var contatore = document.querySelector(
      '[data-contatore-note="' + pazienteId + '"]'
    );
    if (contatore) contatore.textContent = quante;
  }

  function mostraPannelloNota(notaId, quale) {
    nascondiPannelliNota(notaId);
    var selettore =
      quale === "modifica"
        ? '[data-modifica="' + notaId + '"]'
        : '[data-conferma="' + notaId + '"]';
    var pannello = document.querySelector(selettore);
    if (!pannello) return;

    pannello.hidden = false;
    var area = pannello.querySelector("textarea");
    if (area) {
      area.focus();
      // Il cursore va in fondo al testo, non all'inizio: si modifica una
      // nota quasi sempre per aggiungere qualcosa.
      area.setSelectionRange(area.value.length, area.value.length);
    }
  }

  function nascondiPannelliNota(notaId) {
    ['[data-modifica="', '[data-conferma="'].forEach(function (inizio) {
      var pannello = document.querySelector(inizio + notaId + '"]');
      if (pannello) pannello.hidden = true;
    });
  }

  /* I form dentro l'Agenda non ricaricano la pagina: mandano i dati e
     rimettono al loro posto il contenuto aggiornato che torna indietro. */
  document.addEventListener("submit", function (evento) {
    var modulo = evento.target;
    if (modulo.dataset.modulo !== "agenda") return;

    evento.preventDefault();
    caricaAgenda(modulo.action, { method: "POST", body: new FormData(modulo) });
  });

  /* ------------------------------------------------------------------
     CHECKLIST
     ------------------------------------------------------------------ */
  var CHIAVE_CHECKLIST = "cruscotto.checklist.aperta";

  function ripristinaStatoChecklist() {
    var riquadro = document.getElementById("riquadro-checklist");
    if (!riquadro) return;

    // sessionStorage dura quanto la scheda del browser: la preferenza segue
    // il turno di chi sta lavorando e non resta appiccicata al PC condiviso.
    try {
      var salvato = sessionStorage.getItem(CHIAVE_CHECKLIST);
      if (salvato !== null) riquadro.open = salvato === "si";
    } catch (errore) {
      // Se il browser vieta sessionStorage la checklist resta aperta: è una
      // comodità, non deve far fallire nulla.
    }

    riquadro.addEventListener("toggle", function () {
      try {
        sessionStorage.setItem(CHIAVE_CHECKLIST, riquadro.open ? "si" : "no");
      } catch (errore) {
        /* pazienza */
      }
    });
  }

  document.addEventListener("change", function (evento) {
    var casella = evento.target;
    if (casella.dataset.azione !== "spunta") return;

    var contenitore = casella.closest(".voci");
    var etichetta = casella.closest(".voce-check");
    var spuntata = casella.checked;

    etichetta.classList.toggle("fatta", spuntata);

    fetch("/paziente/" + contenitore.dataset.paziente + "/checklist", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": tokenCsrf()
      },
      credentials: "same-origin",
      body: JSON.stringify({ codice: casella.dataset.codice, spuntata: spuntata })
    })
      .then(function (risposta) {
        if (!risposta.ok) throw new Error("risposta " + risposta.status);
        return risposta.json();
      })
      .then(function (dati) {
        aggiornaContatoreChecklist(dati.spuntate, dati.totale);
      })
      .catch(function () {
        // Il segno era già stato messo dal browser: va rimesso com'era,
        // altrimenti l'utente crede di aver salvato qualcosa che non c'è.
        casella.checked = !spuntata;
        etichetta.classList.toggle("fatta", !spuntata);
        avvisa("Non è stato possibile salvare la spunta. Riprova.");
      });
  });

  function aggiornaContatoreChecklist(spuntate, totale) {
    var contatore = document.getElementById("checklist-contatore");
    var barra = document.getElementById("checklist-barra");
    if (!contatore || !barra) return;

    contatore.textContent = spuntate + "/" + totale;
    contatore.classList.toggle("completa", spuntate === totale);
    barra.style.width = (totale ? (spuntate / totale) * 100 : 0) + "%";
  }

  /* ------------------------------------------------------------------
     PIOGGIA DI SIMBOLI (sfondo della pagina di accesso)
     ------------------------------------------------------------------ */
  // Disegni in un riquadro 24x24, nello stile delle icone a tratto.
  var SIMBOLI = [
    // Croce medica
    '<path d="M9 3h6v6h6v6h-6v6H9v-6H3V9h6z"/>',
    // Cuore
    '<path d="M12 20s-7-4.4-9.2-8.6C1.2 8.2 3 4.5 6.6 4.5c2.1 0 3.4 1.2 5.4 3.3 2-2.1 3.3-3.3 5.4-3.3 3.6 0 5.4 3.7 3.8 6.9C19 15.6 12 20 12 20z"/>',
    // Pillola
    '<rect x="2.5" y="8" width="19" height="8" rx="4"/><path d="M12 8v8"/>',
    // Battito cardiaco
    '<path d="M2 12h5l2-5 4 10 2.5-5H22"/>',
    // Goccia
    '<path d="M12 3s6 6.6 6 11a6 6 0 0 1-12 0c0-4.4 6-11 6-11z"/>'
  ];
  // Bianco, giallo e azzurro del logo.
  var COLORI_PIOGGIA = ["#FFFFFF", "#FBE116", "#00A3D4"];

  function tra(minimo, massimo) {
    return minimo + Math.random() * (massimo - minimo);
  }

  function preparaPioggia() {
    var pioggia = document.getElementById("pioggia");
    if (!pioggia) return;

    // Meno simboli sugli schermi stretti, per non affollare.
    var quanti = window.innerWidth < 700 ? 14 : 28;
    for (var i = 0; i < quanti; i++) {
      var simbolo = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      var lato = tra(18, 42);
      simbolo.setAttribute("viewBox", "0 0 24 24");
      simbolo.setAttribute("width", lato);
      simbolo.setAttribute("height", lato);
      simbolo.setAttribute("fill", "none");
      simbolo.setAttribute("stroke", COLORI_PIOGGIA[i % COLORI_PIOGGIA.length]);
      simbolo.setAttribute("stroke-width", "1.8");
      simbolo.setAttribute("stroke-linecap", "round");
      simbolo.setAttribute("stroke-linejoin", "round");
      simbolo.innerHTML = SIMBOLI[Math.floor(Math.random() * SIMBOLI.length)];

      // Gli stili impostati da JavaScript sono ammessi dalla
      // Content-Security-Policy; quelli scritti nell'HTML no.
      var durata = tra(14, 30);
      simbolo.style.left = tra(0, 100) + "%";
      simbolo.style.opacity = tra(0.55, 0.9).toFixed(2);
      simbolo.style.animationDuration = durata + "s";
      // Ritardo negativo: all'apertura i simboli sono già sparsi su tutto
      // lo schermo, invece di partire tutti insieme dal bordo in alto.
      simbolo.style.animationDelay = -tra(0, durata) + "s";
      simbolo.style.setProperty("--deriva", tra(-60, 60) + "px");
      simbolo.style.setProperty("--giro", tra(-240, 240) + "deg");
      pioggia.appendChild(simbolo);
    }
  }

  preparaPioggia();

  /* ------------------------------------------------------------------
     AVVISO TEMPORANEO
     ------------------------------------------------------------------ */
  var timerAvviso = null;

  function avvisa(testo) {
    var avviso = document.getElementById("avviso");
    if (!avviso) return;

    avviso.textContent = testo;
    avviso.classList.add("visibile");

    clearTimeout(timerAvviso);
    timerAvviso = setTimeout(function () {
      avviso.classList.remove("visibile");
    }, 4000);
  }
})();
