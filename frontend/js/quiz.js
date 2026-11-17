document.addEventListener("DOMContentLoaded", () => {
    const quizRound = document.getElementById("quiz-round");
    const quizCorrect = document.getElementById("quiz-correct");
    const quizWrong = document.getElementById("quiz-wrong");
    const quizNext = document.getElementById("quiz-next");
    const quizDetectLink = document.querySelector("#quiz a[href*='main.html']");

    if (!quizRound) return;

    // Exact filenames from frontend/assets/images/real/ and fake/ (1-9 .jpeg, 10-12 .jpg)
    const getExt = (n) => (n <= 9 ? "jpeg" : "jpg");

    const quizPairs = Array.from({ length: 12 }, (_, idx) => {
        const num = idx + 1;
        const ext = getExt(num);
        return {
            real: `./assets/images/real/real_${num}.${ext}`,
            fake: `./assets/images/fake/fake_${num}.${ext}`,
        };
    });

    const shuffle = (arr) => {
        const copy = [...arr];
        for (let i = copy.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [copy[i], copy[j]] = [copy[j], copy[i]];
        }
        return copy;
    };

    let shuffledPairs = shuffle(quizPairs);
    let roundIndex = 0;

    function loadRound() {
        if (roundIndex >= shuffledPairs.length) {
            shuffledPairs = shuffle(quizPairs);
            roundIndex = 0;
        }

        const pair = shuffledPairs[roundIndex];
        const realOnLeft = Math.random() < 0.5;

        const roundSetup = realOnLeft
            ? [
                  { src: pair.real, isReal: "true" },
                  { src: pair.fake, isReal: "false" },
              ]
            : [
                  { src: pair.fake, isReal: "false" },
                  { src: pair.real, isReal: "true" },
              ];

        const cards = quizRound.querySelectorAll(".quiz-card");
        cards.forEach((card, i) => {
            const img = card.querySelector("img");
            img.src = roundSetup[i].src;
            card.dataset.correct = roundSetup[i].isReal;
            card.disabled = false;
        });

        quizCorrect.hidden = true;
        quizWrong.hidden = true;
        quizNext.hidden = true;
    }

    quizRound.querySelectorAll(".quiz-card").forEach((card) => {
        card.addEventListener("click", () => {
            const isReal = card.dataset.correct === "true";

            quizRound.querySelectorAll(".quiz-card").forEach((btn) => {
                btn.disabled = true;
            });

            quizCorrect.hidden = !isReal;
            quizWrong.hidden = isReal;
            quizNext.hidden = false;

            if (quizDetectLink) {
                quizDetectLink.hidden = false;
            }
        });
    });

    if (quizNext) {
        quizNext.addEventListener("click", () => {
            roundIndex++;
            loadRound();
        });
    }

    loadRound();
});