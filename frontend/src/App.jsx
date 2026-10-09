import { useRef, useState } from "react";

import "./App.css";

const API_URL = "http://127.0.0.1:8000";
function App() {
  
  const sakuraPetals = Array.from({ length: 22 }, (_, i) => ({
    id: i,
    left: `${(i * 47 + 13) % 100}%`,
    delay: `${-((i * 7) % 18)}s`,
    duration: `${12 + ((i * 5) % 10)}s`,
    size: `${12 + ((i * 3) % 13)}px`,
    drift: `${((i * 37) % 140) - 70}px`,
  }));

  // =========================================================
  // GENERAL
  // =========================================================
const [dailyGoal, setDailyGoal] = useState(10);
const [studyStreak, setStudyStreak] = useState(() =>
  Number(localStorage.getItem("japaneseStudyStreak") || 0)
);
const [wordsReviewedToday, setWordsReviewedToday] =
  useState(() => {
    const today = new Date().toLocaleDateString("en-CA");
    const saved = JSON.parse(
      localStorage.getItem("japaneseDailyGoal") || "{}"
    );

    return saved.date === today ? saved.count : 0;
  });
  const [page, setPage] = useState("analyze");
  
const [listeningLevel, setListeningLevel] = useState("N5");
const [listeningQuestions, setListeningQuestions] = useState([]);
const [listeningIndex, setListeningIndex] = useState(0);
const [listeningSelectedAnswer, setListeningSelectedAnswer] = useState(null);
const [listeningShowTranscript, setListeningShowTranscript] = useState(false);
const [listeningScore, setListeningScore] = useState(0);
const [listeningLoading, setListeningLoading] = useState(false);
const [listeningError, setListeningError] = useState("");
const [listeningFinished, setListeningFinished] = useState(false);

const [smartReviewWords, setSmartReviewWords] = useState([]);
const [smartReviewIndex, setSmartReviewIndex] = useState(0);
const [smartReviewShowAnswer, setSmartReviewShowAnswer] = useState(false);
const [smartReviewLoading, setSmartReviewLoading] = useState(false);
const [smartReviewError, setSmartReviewError] = useState("");
const [smartReviewComplete, setSmartReviewComplete] = useState(false);
  // =========================================================
  // ANALYZE
  // =========================================================

  const [sentence, setSentence] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);

  const [selectedWord, setSelectedWord] = useState(null);
  const [savingWord, setSavingWord] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");

  // =========================================================
  // VOCABULARY
  // =========================================================

  const [vocabulary, setVocabulary] = useState([]);
  const [vocabularyLoading, setVocabularyLoading] = useState(false);
  const [vocabularyError, setVocabularyError] = useState("");
  const [search, setSearch] = useState("");

  // =========================================================
  // FLASHCARDS
  // =========================================================

  const [practiceIndex, setPracticeIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [practiceScore, setPracticeScore] = useState(0);
  const [practiceStarted, setPracticeStarted] = useState(false);

  // =========================================================
  // QUIZ
  // =========================================================

  const [quizStarted, setQuizStarted] = useState(false);
  const [quizWords, setQuizWords] = useState([]);
  const [quizIndex, setQuizIndex] = useState(0);
  const [quizScore, setQuizScore] = useState(0);
  const [quizOptions, setQuizOptions] = useState([]);
  const [selectedAnswer, setSelectedAnswer] = useState(null);

  // =========================================================
  // PROGRESS
  // =========================================================

  const [quizHistory, setQuizHistory] = useState(() => {
    try {
      const saved = localStorage.getItem(
        "languageTutorQuizHistory"
      );

      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

 
  // =========================================================
  // TEXT TO SPEECH
  // =========================================================

  const speakJapanese = (text, rate = 1) => {
    if (!("speechSynthesis" in window)) {
      alert("Speech synthesis is not supported in this browser.");
      return;
    }

    const playAudio = () => {
      const voices = window.speechSynthesis.getVoices();

      const japaneseVoice =
        voices.find(
          (voice) => voice.lang.toLowerCase() === "ja-jp"
        ) ||
        voices.find((voice) =>
          voice.lang.toLowerCase().startsWith("ja")
        );

      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "ja-JP";
      utterance.rate = rate;
      utterance.pitch = 1;

      if (japaneseVoice) {
        utterance.voice = japaneseVoice;
      }

      window.speechSynthesis.speak(utterance);
    };

    const voices = window.speechSynthesis.getVoices();

    if (voices.length > 0) {
      playAudio();
    } else {
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.onvoiceschanged = null;
        playAudio();
      };
    }
  };


  // =========================================================
  // SPEECH TO TEXT
  // =========================================================

  const startJapaneseListening = () => {
    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert(
        "Speech recognition is not supported in this browser. Please use Microsoft Edge."
      );

      return;
    }

    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }

    const recognition =
      new SpeechRecognition();

    recognition.lang = "ja-JP";
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
      setError("");
    };

    recognition.onresult = (event) => {
      const transcript =
        event.results[0][0].transcript.trim();

      if (!transcript) {
        setError(
          "I couldn't hear any Japanese. Please try again."
        );

        return;
      }

      setSentence(transcript);

      analyzeSentence(transcript);
    };

    recognition.onerror = (event) => {
      console.error(
        "Speech recognition error:",
        event
      );

      if (event.error === "not-allowed") {
        setError(
          "Microphone permission was blocked. Please allow microphone access in Edge."
        );
      } else if (event.error === "no-speech") {
        setError(
          "I couldn't hear you. Please try speaking again."
        );
      } else {
        setError(
          `Speech recognition error: ${event.error}`
        );
      }

      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
      recognitionRef.current = null;
    };

    recognitionRef.current = recognition;

    recognition.start();
  };

  const stopJapaneseListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }

    setIsListening(false);
  };

  // =========================================================
  // ANALYZE SENTENCE
  // =========================================================

  const analyzeSentence = async (
    textToAnalyze = sentence
  ) => {
    if (!textToAnalyze.trim()) {
      setError("Please enter a sentence.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);
    setSelectedWord(null);
    setSaveMessage("");

    try {
      const response = await fetch(
        `${API_URL}/analyze`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            target_language: "Japanese",
            known_language: "English",
            text: textToAnalyze,
          }),
        }
      );

      if (!response.ok) {
        const errorText =
          await response.text();

        console.error(
          "Analyze error:",
          response.status,
          errorText
        );

        throw new Error(
          `Failed to analyze sentence (${response.status})`
        );
      }

      const data =
        await response.json();

      setResult(data);
    } catch (err) {
      console.error(err);

      setError(
        "Could not analyze the sentence. Make sure FastAPI is running."
      );
    } finally {
      setLoading(false);
    }
  };

  // =========================================================
  // SAVE VOCABULARY
  // =========================================================

  const saveWord = async () => {
    if (!selectedWord) {
      return;
    }

    setSavingWord(true);
    setSaveMessage("");

    try {
      const response = await fetch(
        `${API_URL}/vocabulary`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            word: selectedWord.word,
            reading:
              selectedWord.reading || "",
            romaji:
              selectedWord.romaji || "",
            meaning:
              selectedWord.meaning || "",
            part_of_speech:
              selectedWord.part_of_speech ||
              "",
            role:
              selectedWord.role || "",

            target_language: "Japanese",
            known_language: "English",
          }),
        }
      );

      if (!response.ok) {
        const errorText =
          await response.text();

        console.error(
          "Vocabulary save error:",
          response.status,
          errorText
        );

        throw new Error(
          `Failed to save word (${response.status})`
        );
      }

      const data =
        await response.json();

      setSaveMessage(
        data.message ||
          "Word saved successfully."
      );

      loadVocabulary();
    } catch (err) {
      console.error(err);

      setSaveMessage(
        "Could not save the word."
      );
    } finally {
      setSavingWord(false);
    }
  };

  // =========================================================
  // LOAD VOCABULARY
  // =========================================================

  const loadVocabulary = async () => {
    setVocabularyLoading(true);
    setVocabularyError("");

    try {
      const response = await fetch(
        `${API_URL}/vocabulary`
      );

      if (!response.ok) {
        throw new Error(
          "Failed to load vocabulary."
        );
      }

      const data =
        await response.json();

      setVocabulary(
        data.vocabulary || []
      );
    } catch (err) {
      console.error(err);

      setVocabularyError(
        "Could not load vocabulary. Make sure the backend is running."
      );
    } finally {
      setVocabularyLoading(false);
    }
  };

  // =========================================================
  // SMART REVIEW
  // =========================================================

  const loadSmartReview = async () => {
    setSmartReviewLoading(true);
    setSmartReviewError("");
    setSmartReviewWords([]);
    setSmartReviewIndex(0);
    setSmartReviewShowAnswer(false);
    setSmartReviewComplete(false);

    try {
      const response = await fetch(
        `${API_URL}/vocabulary/weak`
      );

      if (!response.ok) {
        throw new Error("Failed to load weak vocabulary.");
      }

      const data = await response.json();

      const words = (data.vocabulary || []).filter(
        (word) =>
          word.reviewable === 1 &&
          word.word?.trim() &&
          word.meaning?.trim()
      );

      setSmartReviewWords(words);

      if (words.length === 0) {
        setSmartReviewError(
          "No words need review right now. Save some Japanese vocabulary first."
        );
      }
    } catch (err) {
      console.error("Smart Review loading error:", err);

      setSmartReviewError(
        "Could not load Smart Review. Make sure your backend is running."
      );
    } finally {
      setSmartReviewLoading(false);
    }
  };
const recordWordReviewedToday = () => {
  const today = new Date().toLocaleDateString("en-CA");

  // Update today's review count
  const saved = JSON.parse(
    localStorage.getItem("japaneseDailyGoal") || "{}"
  );

  const currentCount =
    saved.date === today ? saved.count : 0;

  const newCount = currentCount + 1;

  localStorage.setItem(
    "japaneseDailyGoal",
    JSON.stringify({
      date: today,
      count: newCount,
    })
  );

  setWordsReviewedToday(newCount);

  // Update the study streak
  const streakData = JSON.parse(
    localStorage.getItem("japaneseStudyDays") || "{}"
  );

  const previousDate = streakData.lastDate;

  let newStreak = Number(
    localStorage.getItem("japaneseStudyStreak") || 0
  );

  if (previousDate !== today) {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);

    const yesterdayKey =
      yesterday.toLocaleDateString("en-CA");

    if (previousDate === yesterdayKey) {
      newStreak += 1;
    } else {
      newStreak = 1;
    }

    localStorage.setItem(
      "japaneseStudyStreak",
      String(newStreak)
    );

    localStorage.setItem(
      "japaneseStudyDays",
      JSON.stringify({
        lastDate: today,
      })
    );
  }

  
  setStudyStreak(newStreak);
};

const answerSmartReview = async (knewWord) => {

    const currentWord =
      smartReviewWords[smartReviewIndex];

    if (!currentWord) {
      return;
    }

    setSmartReviewError("");

    try {
      const response = await fetch(
        `${API_URL}/vocabulary/review`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            vocabulary_id: currentWord.id,
            correct: knewWord,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to save review result.");
      }
      
      recordWordReviewedToday();
      setSmartReviewShowAnswer(false);

      if (
        smartReviewIndex + 1 >=
        smartReviewWords.length
      ) {
        setSmartReviewComplete(true);
      } else {
        setSmartReviewIndex((previous) => previous + 1);
      }
    } catch (err) {
      console.error("Smart Review answer error:", err);

      setSmartReviewError(
        "Could not save your answer. Please try again."
      );
    }
  };

  // =========================================================
  // NAVIGATION
  // =========================================================

  const openAnalyzer = () => {
    setPage("analyze");
  };

  const openVocabulary = () => {
    setPage("vocabulary");
    loadVocabulary();
  };

  const openPractice = () => {
    setPage("practice");

    loadVocabulary();

    setPracticeStarted(false);
    setQuizStarted(false);
    setShowAnswer(false);
    setSelectedAnswer(null);
  };

  const openProgress = () => {
    setPage("progress");
    loadVocabulary();
  };

const openSmartReview = () => {
  setPage("smart-review");
  loadSmartReview();
};

const openListening = () => {
  setPage("listening");
  setListeningQuestions([]);
  setListeningIndex(0);
  setListeningSelectedAnswer(null);
  setListeningShowTranscript(false);
  setListeningScore(0);
  setListeningError("");
  setListeningFinished(false);
};


const generateListeningQuestions = async () => {
  setListeningLoading(true);
  setListeningError("");
  setListeningQuestions([]);
  setListeningIndex(0);
  setListeningSelectedAnswer(null);
  setListeningShowTranscript(false);
  setListeningScore(0);
  setListeningFinished(false);

  try {
    const response = await fetch(`${API_URL}/listening/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        level: listeningLevel,
        count: 5,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Could not generate listening questions.");
    }

    if (!Array.isArray(data.questions) || data.questions.length === 0) {
      throw new Error("No listening questions were returned.");
    }

    setListeningQuestions(data.questions);
  } catch (err) {
    console.error("Listening generation error:", err);
    setListeningError(
      err.message || "Could not connect to the backend."
    );
  } finally {
    setListeningLoading(false);
  }
};

const answerListeningQuestion = (option) => {
  if (listeningSelectedAnswer !== null) return;

  setListeningSelectedAnswer(option);

  const currentQuestion = listeningQuestions[listeningIndex];

  if (option === currentQuestion.answer) {
    setListeningScore((previous) => previous + 1);
  }
};

const nextListeningQuestion = () => {
  if (listeningIndex + 1 >= listeningQuestions.length) {
    setListeningFinished(true);
    return;
  }

  setListeningIndex((previous) => previous + 1);
  setListeningSelectedAnswer(null);
  setListeningShowTranscript(false);
};

  // =========================================================
  // FLASHCARD PRACTICE
  // =========================================================

  const startPractice = async () => {
    try {
      const response = await fetch(
        `${API_URL}/vocabulary`
      );

      if (!response.ok) {
        throw new Error(
          "Failed to load vocabulary."
        );
      }

      const data =
        await response.json();

      const words =
        (data.vocabulary || []).filter(
          (word) =>
            word.reviewable === 1 &&
            word.meaning &&
            word.meaning.trim() !== ""
        );

      setVocabulary(words);

      if (words.length === 0) {
        return;
      }

      setPracticeIndex(0);
      setPracticeScore(0);
      setShowAnswer(false);
      setPracticeStarted(true);
      setQuizStarted(false);
    } catch (err) {
      console.error(err);
    }
  };

  const answerPractice = (known) => {
    if (known) {
      setPracticeScore(
        (previous) => previous + 1
      );
    }

    setShowAnswer(false);

    setPracticeIndex(
      (previous) => previous + 1
    );
  };

  // =========================================================
  // QUIZ HELPERS
  // =========================================================

  const isValidQuizWord = (word) => {
    if (!word) {
      return false;
    }

    // Must explicitly be marked as reviewable.
    if (word.reviewable !== 1) {
      return false;
    }

    // Must have a real meaning.
    if (
      !word.meaning ||
      !word.meaning.trim()
    ) {
      return false;
    }

    // Must have a word.
    if (
      !word.word ||
      !word.word.trim()
    ) {
      return false;
    }

    return true;
  };

  const generateQuizOptions = (
    correctWord,
    allWords
  ) => {
    const validWords =
      allWords.filter(
        isValidQuizWord
      );

    const otherWords =
      validWords
        .filter(
          (word) =>
            word.id !==
            correctWord.id
        )
        .sort(
          () =>
            Math.random() - 0.5
        )
        .slice(0, 3);

    const options = [
      correctWord,
      ...otherWords,
    ].sort(
      () =>
        Math.random() - 0.5
    );

    setQuizOptions(options);
  };

  // =========================================================
  // START QUIZ
  // =========================================================

  const startQuiz = async () => {
    try {
      // -----------------------------------------------------
      // Get all vocabulary
      // -----------------------------------------------------

      const vocabularyResponse =
        await fetch(
          `${API_URL}/vocabulary`
        );

      if (!vocabularyResponse.ok) {
        throw new Error(
          "Failed to load vocabulary."
        );
      }

      const vocabularyData =
        await vocabularyResponse.json();

      const allVocabulary =
        vocabularyData.vocabulary ||
        [];

      // -----------------------------------------------------
      // IMPORTANT:
      // Only reviewable words with meanings
      // -----------------------------------------------------

      const validWords =
        allVocabulary.filter(
          isValidQuizWord
        );

      // -----------------------------------------------------
      // Need at least 4 words for
      // multiple-choice questions.
      // -----------------------------------------------------

      if (validWords.length < 4) {
        setQuizStarted(false);

        alert(
          `You need at least 4 reviewable vocabulary words with meanings. You currently have ${validWords.length}.`
        );

        return;
      }

      // -----------------------------------------------------
      // Get weak vocabulary
      // -----------------------------------------------------

      let weakWords = [];

      try {
        const weakResponse =
          await fetch(
            `${API_URL}/vocabulary/weak`
          );

        if (weakResponse.ok) {
          const weakData =
            await weakResponse.json();

          weakWords =
            (weakData.vocabulary ||
              []).filter(
                isValidQuizWord
              );
        }
      } catch (err) {
        console.error(
          "Could not load weak vocabulary:",
          err
        );
      }

      // -----------------------------------------------------
      // Remove duplicates
      // -----------------------------------------------------

      const weakIds =
        new Set(
          weakWords.map(
            (word) => word.id
          )
        );

      // -----------------------------------------------------
      // Put weak words FIRST
      // -----------------------------------------------------

      const remainingWords =
        validWords
          .filter(
            (word) =>
              !weakIds.has(
                word.id
              )
          )
          .sort(
            () =>
              Math.random() - 0.5
          );

      const prioritizedWords = [
        ...weakWords,
        ...remainingWords,
      ];

      // -----------------------------------------------------
      // Shuffle weak words among themselves
      // while keeping them prioritized.
      // -----------------------------------------------------

      const weakShuffled =
        [...weakWords].sort(
          () =>
            Math.random() - 0.5
        );

      const remainingShuffled =
        [...remainingWords].sort(
          () =>
            Math.random() - 0.5
        );

      const combinedWords = [
        ...weakShuffled,
        ...remainingShuffled,
      ];

      // -----------------------------------------------------
      // Maximum 10 questions
      // -----------------------------------------------------

      const selectedQuizWords =
        combinedWords.slice(
          0,
          Math.min(
            10,
            combinedWords.length
          )
        );

      // -----------------------------------------------------
      // Final safety check
      // -----------------------------------------------------

      const finalQuizWords =
        selectedQuizWords.filter(
          isValidQuizWord
        );

      if (finalQuizWords.length < 4) {
        alert(
          "There are not enough valid reviewable words for the quiz."
        );

        return;
      }

      setVocabulary(
        allVocabulary
      );

      setQuizWords(
        finalQuizWords
      );

      setQuizIndex(0);
      setQuizScore(0);
      setSelectedAnswer(null);
      setQuizStarted(true);
      setPracticeStarted(false);

      generateQuizOptions(
        finalQuizWords[0],
        validWords
      );
    } catch (err) {
      console.error(
        "Quiz start error:",
        err
      );

      alert(
        "Could not start the quiz. Make sure the backend is running."
      );
    }
  };

  // =========================================================
  // SELECT QUIZ ANSWER
  // =========================================================

  const selectQuizAnswer = async (
    option
  ) => {
    if (selectedAnswer) {
      return;
    }

    setSelectedAnswer(option);

    const currentWord =
      quizWords[quizIndex];

    const isCorrect =
      option.id === currentWord.id;

    if (isCorrect) {
      setQuizScore(
        (previous) =>
          previous + 1
      );
    }

    // -------------------------------------------------------
    // Save result to backend
    // -------------------------------------------------------

    try {
      await fetch(
        `${API_URL}/vocabulary/review`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            vocabulary_id:
              currentWord.id,

            correct: isCorrect,
          }),
        }
      );
    } catch (err) {
      console.error(
        "Could not save review result:",
        err
      );
    }
  };

  // =========================================================
  // SAVE QUIZ RESULT
  // =========================================================

  const saveQuizResult = (
    finalScore
  ) => {
    const result = {
      id: Date.now(),

      score: finalScore,

      total:
        quizWords.length,

      percentage:
        quizWords.length > 0
          ? Math.round(
              (finalScore /
                quizWords.length) *
                100
            )
          : 0,

      date:
        new Date().toLocaleDateString(),
    };

    const updatedHistory = [
      result,
      ...quizHistory,
    ];

    setQuizHistory(
      updatedHistory
    );

    localStorage.setItem(
      "languageTutorQuizHistory",
      JSON.stringify(
        updatedHistory
      )
    );
  };

  // =========================================================
  // NEXT QUIZ QUESTION
  // =========================================================

  const nextQuizQuestion = () => {
    const nextIndex =
      quizIndex + 1;

    // -------------------------------------------------------
    // FINAL QUESTION
    // -------------------------------------------------------

    if (
      nextIndex >=
      quizWords.length
    ) {
      const lastQuestionCorrect =
        selectedAnswer &&
        selectedAnswer.id ===
          quizWords[
            quizIndex
          ].id;

      const finalScore =
        quizScore +
        (lastQuestionCorrect
          ? 1
          : 0);

      saveQuizResult(
        finalScore
      );

      setQuizIndex(
        nextIndex
      );

      setSelectedAnswer(
        null
      );

      return;
    }

    // -------------------------------------------------------
    // NEXT QUESTION
    // -------------------------------------------------------

    setQuizIndex(
      nextIndex
    );

    setSelectedAnswer(
      null
    );

    const validWords =
      vocabulary.filter(
        isValidQuizWord
      );

    generateQuizOptions(
      quizWords[nextIndex],
      validWords
    );
  };

  // =========================================================
  // PROGRESS CALCULATIONS
  // =========================================================

  const totalQuizQuestions =
    quizHistory.reduce(
      (total, quiz) =>
        total + quiz.total,
      0
    );

  const totalCorrectAnswers =
    quizHistory.reduce(
      (total, quiz) =>
        total + quiz.score,
      0
    );

  const overallAccuracy =
    totalQuizQuestions > 0
      ? Math.round(
          (totalCorrectAnswers /
            totalQuizQuestions) *
            100
        )
      : 0;

  // =========================================================
  // FILTER VOCABULARY
  // =========================================================

  const filteredVocabulary =
    vocabulary.filter(
      (item) => {
        const query =
          search.toLowerCase();

        return (
          item.word
            ?.toLowerCase()
            .includes(query) ||
          item.reading
            ?.toLowerCase()
            .includes(query) ||
          item.romaji
            ?.toLowerCase()
            .includes(query) ||
          item.meaning
            ?.toLowerCase()
            .includes(query)
        );
      }
    );

  // =========================================================
  // UI
  // =========================================================

  return (
  <div className="app">
    <div className="sakura-background" aria-hidden="true">
      {sakuraPetals.map((petal) => (
        <span
          key={petal.id}
          className="sakura-petal"
          style={{
            left: petal.left,
            animationDelay: petal.delay,
            animationDuration: petal.duration,
            fontSize: petal.size,
            "--drift": petal.drift,
          }}
        >
          🌸
        </span>
      ))}
    </div>

      {/* =====================================================
          HEADER
      ===================================================== */}

           <aside className="sidebar">

        <div className="sidebar-logo" onClick={openAnalyzer}>
          <span className="sidebar-logo-icon">✿</span>
          <span>AI Language Tutor</span>
        </div>

        <div className="sidebar-section-label">
          LEARNING
        </div>

        <nav className="sidebar-navigation">

          <button
            className={page === "analyze" ? "nav-button active" : "nav-button"}
            onClick={openAnalyzer}
          >
            <span className="sidebar-icon">✎</span>
            <span>Analyze</span>
          </button>

          <button
            className={page === "vocabulary" ? "nav-button active" : "nav-button"}
            onClick={openVocabulary}
          >
            <span className="sidebar-icon">文</span>
            <span>Vocabulary</span>
          </button>

          <button
            className={page === "practice" ? "nav-button active" : "nav-button"}
            onClick={openPractice}
          >
            <span className="sidebar-icon">✧</span>
            <span>Practice</span>
          </button>

          <button
            className={page === "smart-review" ? "nav-button active" : "nav-button"}
            onClick={openSmartReview}
          >
            <span className="sidebar-icon">↻</span>
            <span>Smart Review</span>
          </button>

          <button
            className={page === "listening" ? "nav-button active" : "nav-button"}
            onClick={openListening}
          >
            <span className="sidebar-icon">♫</span>
            <span>Listening</span>
          </button>

          <button
            className={page === "progress" ? "nav-button active" : "nav-button"}
            onClick={openProgress}
          >
            <span className="sidebar-icon">▥</span>
            <span>Progress</span>
          </button>

        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-language-badge">
            <span>🌸</span>
            <div>
              <strong>Learning Japanese</strong>
              <small>日本語を学ぼう</small>
            </div>
          </div>
        </div>

      </aside>

      {/* =====================================================
          ANALYZE PAGE
      ===================================================== */}

      {page === "analyze" && (

        <main className="container">
                    <section className="dashboard-overview">

            <div className="dashboard-welcome">
              <p className="eyebrow">YOUR LEARNING SPACE</p>
              <h2>こんにちは！ 👋</h2>
              <p>Small steps every day lead to fluent Japanese.</p>
            </div>

            <div className="dashboard-stats">

              <div className="dashboard-stat">
  <span className="dashboard-stat-icon">🎯</span>
  <span className="dashboard-stat-label">Daily Goal</span>

  <strong>
    {wordsReviewedToday} / {dailyGoal}
  </strong>

  <div className="goal-progress-track">
    <div
      className="goal-progress-fill"
      style={{
        width: `${Math.min(
          (wordsReviewedToday / dailyGoal) * 100,
          100
        )}%`,
      }}
    />
  </div>

  <small>Words reviewed today</small>
</div>

             <button
  type="button"
  className="dashboard-stat dashboard-stat-button"
  onClick={openVocabulary}
>
  <span className="dashboard-stat-icon">📚</span>
  <span className="dashboard-stat-label">Vocabulary</span>
  <strong>
  {vocabulary.filter(
    (word) =>
      word.reviewable === 1 &&
      word.word?.trim() &&
      word.meaning?.trim()
  ).length} words
</strong>
  <small>View your saved vocabulary →</small>
</button>

             <div className="dashboard-stat">
  <span className="dashboard-stat-icon">🔥</span>
  <span className="dashboard-stat-label">Study Streak</span>
  <strong>Keep it going!</strong>
  <small>Review words every day</small>
</div>

            </div>

          </section>

          <section className="hero">

            <p className="eyebrow">
              JAPANESE LANGUAGE LEARNING
            </p>

            <h1>
              Understand every
              <br />
              Japanese sentence.
            </h1>

            <p className="hero-description">
              Enter a Japanese sentence and get a
              learner-friendly breakdown of vocabulary,
              grammar, translation, and corrections.
            </p>

          </section>

          <section className="analyzer-card">

            <textarea
              value={sentence}
              onChange={(event) =>
                setSentence(
                  event.target.value
                )
              }
              placeholder="例：私は学校に行きます。"
              rows={4}
            />

            <div className="analyzer-footer">

              <span>
                Japanese → English
              </span>

              <button
                type="button"
                onClick={
                  isListening
                    ? stopJapaneseListening
                    : startJapaneseListening
                }
                disabled={loading}
              >
                {isListening
                  ? "🛑 Stop"
                  : "🎤 Speak Japanese"}
              </button>

              <button
                type="button"
                onClick={() =>
                  analyzeSentence(
                    sentence
                  )
                }
                disabled={loading}
              >
                {loading
                  ? "Analyzing..."
                  : "Analyze Sentence →"}
              </button>

            </div>

          </section>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {result && (

            <section className="results">

              {/* JAPANESE SENTENCE */}

              <div className="result-card speech-card">

                <div className="result-label">
                  JAPANESE SENTENCE
                </div>

                <div className="speech-sentence">
                  {result.sentence ||
                    sentence}
                </div>

                <button
                  className="speak-button"
                  onClick={() =>
                    speakJapanese(
                      result.sentence ||
                        sentence
                    )
                  }
                >
                  🔊 Hear Japanese
                </button>

              </div>

              {/* TRANSLATION */}

              <div className="result-card">

                <div className="result-label">
                  TRANSLATION
                </div>

                <div className="translation">
                  {result.translation}
                </div>

              </div>

              {/* CORRECTION */}

              {result.natural === false &&
                result.correction && (

                  <div className="result-card correction-card">

                    <div className="result-label">
                      CORRECTION
                    </div>

                    <div className="correction">
                      {result.correction}
                    </div>

                    {result.correction_explanation && (

                      <p>
                        {
                          result.correction_explanation
                        }
                      </p>

                    )}

                  </div>

                )}

              {/* WORD BREAKDOWN */}

              <div className="result-card">

                <div className="result-label">
                  WORD BREAKDOWN
                </div>

                <p className="result-hint">
                  Click a word to view its details
                  and save it to your vocabulary.
                </p>

                <div className="word-grid">

                  {result.words?.map(
                    (word, index) => (

                      <button
                        key={index}
                        className="word-item"
                        onClick={() => {
                          setSelectedWord(
                            word
                          );

                          setSaveMessage("");
                        }}
                      >

                        <span className="word-main">
                          {word.word}
                        </span>

                        {word.reading && (
                          <span className="word-reading">
                            {word.reading}
                          </span>
                        )}

                        {word.romaji && (
                          <span className="word-romaji">
                            {word.romaji}
                          </span>
                        )}

                        {word.meaning && (
                          <span className="word-meaning">
                            {word.meaning}
                          </span>
                        )}

                      </button>

                    )
                  )}

                </div>

              </div>

              {/* GRAMMAR */}

              {result.grammar?.length > 0 && (

                <div className="result-card">

                  <div className="result-label">
                    GRAMMAR
                  </div>

                  <div className="grammar-list">

                    {result.grammar.map(
                      (grammar, index) => (

                        <div
                          className="grammar-item"
                          key={index}
                        >

                          <div className="grammar-pattern">
                            {grammar.pattern}
                          </div>

                          <div className="grammar-meaning">
                            {grammar.meaning}
                          </div>

                          <p>
                            {
                              grammar.explanation
                            }
                          </p>

                        </div>

                      )
                    )}

                  </div>

                </div>

              )}

              {/* EXAMPLES */}

              {result.examples?.length > 0 && (

                <div className="result-card">

                  <div className="result-label">
                    EXAMPLES
                  </div>

                  <div className="examples-list">

                    {result.examples.map(
                      (example, index) => (

                        <div
                          className="example-item"
                          key={index}
                        >

                          <div className="example-sentence">
                            {
                              example.sentence
                            }
                          </div>

                          <div className="example-translation">
                            {
                              example.translation
                            }
                          </div>

                          <p>
                            {
                              example.explanation
                            }
                          </p>

                        </div>

                      )
                    )}

                  </div>

                </div>

              )}

            </section>

          )}

        </main>

      )}

      {/* =====================================================
          SMART REVIEW PAGE
      ===================================================== */}

      {page === "smart-review" && (
        <main className="container smart-review-page">
          <section className="smart-review-header">
            <p className="eyebrow">PERSONALIZED PRACTICE</p>
            <h1>Smart Review</h1>
            <p>
              Review words you find difficult and strengthen
              your Japanese vocabulary.
            </p>
          </section>

          {smartReviewLoading && (
            <div className="smart-review-message">
              Loading your review cards...
            </div>
          )}

          {!smartReviewLoading && smartReviewError && (
            <div className="smart-review-message">
              <p>{smartReviewError}</p>

              <button
                className="smart-review-primary"
                onClick={loadSmartReview}
              >
                Try again
              </button>
            </div>
          )}

          {!smartReviewLoading &&
            !smartReviewError &&
            smartReviewComplete && (
              <section className="smart-review-complete">
                <div className="smart-review-icon">🎉</div>
                <h2>Review complete!</h2>
                <p>
                  You've reviewed all {smartReviewWords.length}{" "}
                  {smartReviewWords.length === 1 ? "word" : "words"}.
                </p>

                <button
                  className="smart-review-primary"
                  onClick={loadSmartReview}
                >
                  Review again
                </button>
              </section>
            )}

          {!smartReviewLoading &&
            !smartReviewError &&
            !smartReviewComplete &&
            smartReviewWords.length > 0 &&
            smartReviewWords[smartReviewIndex] && (
              <section className="smart-review-card">
                <div className="smart-review-progress-header">
                  <span>Today's review</span>

                  <span>
                    {smartReviewIndex + 1} /{" "}
                    {smartReviewWords.length}
                  </span>
                </div>

                <div className="smart-review-progress-track">
                  <div
                    className="smart-review-progress-fill"
                    style={{
                      width: `${
                        ((smartReviewIndex + 1) /
                          smartReviewWords.length) *
                        100
                      }%`,
                    }}
                  />
                </div>

                <div className="smart-review-word">
                  {smartReviewWords[smartReviewIndex].word}
                </div>

                {smartReviewShowAnswer && (
                  <div className="smart-review-answer">
                    {smartReviewWords[smartReviewIndex].reading && (
                      <p className="smart-review-reading">
                        {smartReviewWords[smartReviewIndex].reading}
                      </p>
                    )}

                    {smartReviewWords[smartReviewIndex].romaji && (
                      <p className="smart-review-romaji">
                        {smartReviewWords[smartReviewIndex].romaji}
                      </p>
                    )}

                    <p className="smart-review-meaning">
                      {smartReviewWords[smartReviewIndex].meaning}
                    </p>

                    <button
                      className="smart-review-audio"
                      onClick={() =>
                        speakJapanese(
                          smartReviewWords[smartReviewIndex].word
                        )
                      }
                    >
                      🔊 Hear pronunciation
                    </button>
                  </div>
                )}

                {!smartReviewShowAnswer ? (
                  <button
                    className="smart-review-primary smart-review-reveal"
                    onClick={() => setSmartReviewShowAnswer(true)}
                  >
                    Show answer
                  </button>
                ) : (
                  <div className="smart-review-actions">
                    <button
                      className="smart-review-again"
                      onClick={() => answerSmartReview(false)}
                    >
                      Again
                    </button>

                    <button
                      className="smart-review-known"
                      onClick={() => answerSmartReview(true)}
                    >
                      Got it
                    </button>
                  </div>
                )}

                <p className="smart-review-hint">
                  Try to remember the meaning before revealing
                  the answer.
                </p>
              </section>
            )}
        </main>
      )}

{/* =====================================================
    LISTENING PRACTICE PAGE
===================================================== */}

{page === "listening" && (
  <main className="container listening-page">
    <section className="listening-header">
      <p className="eyebrow">JAPANESE LISTENING</p>
      <h1>Listening Practice</h1>
      <p>
        Listen carefully, understand the sentence, and choose
        the correct English meaning.
      </p>
    </section>

    {!listeningQuestions.length && !listeningLoading && (
      <section className="listening-card">
        <label htmlFor="listening-level">JLPT level</label>

        <select
          id="listening-level"
          value={listeningLevel}
          onChange={(event) => setListeningLevel(event.target.value)}
        >
          <option value="N5">N5 — Beginner</option>
          <option value="N4">N4 — Elementary</option>
          <option value="N3">N3 — Intermediate</option>
          <option value="N2">N2 — Upper intermediate</option>
          <option value="N1">N1 — Advanced</option>
        </select>

       



        <button
          className="practice-start-button"
          onClick={generateListeningQuestions}
        >
          Start Listening Practice
        </button>
      </section>
    )}

    {listeningLoading && (
      <div className="listening-card">
        Generating your listening exercises...
      </div>
    )}

    {listeningError && (
      <div className="error-message">{listeningError}</div>
    )}

    {listeningFinished && (
      <section className="listening-card listening-results">
        <h2>Practice complete!</h2>
        <p>
          Your score: {listeningScore} / {listeningQuestions.length}
        </p>
        <button
          className="practice-start-button"
          onClick={generateListeningQuestions}
        >
          Try Again
        </button>
      </section>
    )}

    {!listeningLoading &&
      !listeningFinished &&
      listeningQuestions.length > 0 &&
      listeningQuestions[listeningIndex] && (
        <section className="listening-card">
          <div className="listening-progress">
            Question {listeningIndex + 1} of {listeningQuestions.length}
            {" · "}Score: {listeningScore}
          </div>

          <h2>Listen to the Japanese sentence</h2>

          

<button
  className="speak-button"
  onClick={() =>
    speakJapanese(listeningQuestions[listeningIndex].sentence)
  }
>
  🔊 Play Audio
</button>

<button
  className="speak-button"
  onClick={() =>
    speakJapanese(
      listeningQuestions[listeningIndex].sentence,
      0.65
    )
  }
>
  🐢 Slow Audio
</button>



          <p>What does the sentence mean?</p>

          <div className="listening-options">
            {listeningQuestions[listeningIndex].options.map(
              (option, index) => {
                const correct =
                  option === listeningQuestions[listeningIndex].answer;
                const selected = option === listeningSelectedAnswer;

                let optionClass = "listening-option";

                if (listeningSelectedAnswer !== null && correct) {
                  optionClass += " correct";
                } else if (selected && !correct) {
                  optionClass += " incorrect";
                }

                return (
                  <button
                    key={`${index}-${option}`}
                    className={optionClass}
                    onClick={() => answerListeningQuestion(option)}
                    disabled={listeningSelectedAnswer !== null}
                  >
                    {option}
                  </button>
                );
              }
            )}
          </div>

          {listeningSelectedAnswer !== null && (
            <div className="listening-feedback">
              <h3>
                {listeningSelectedAnswer ===
                listeningQuestions[listeningIndex].answer
                  ? "Correct! 🎉"
                  : "Not quite. Keep practising!"}
              </h3>

              <p>
                {listeningQuestions[listeningIndex].explanation}
              </p>

              {!listeningShowTranscript ? (
                <button
                  className="show-answer-button"
                  onClick={() => setListeningShowTranscript(true)}
                >
                  Reveal Transcript
                </button>
              ) : (
                <div className="listening-transcript">
                  <h3>
                    {listeningQuestions[listeningIndex].sentence}
                  </h3>
                  <p>
                    {listeningQuestions[listeningIndex].reading}
                  </p>
                  <p>
                    {listeningQuestions[listeningIndex].romaji}
                  </p>
                  <p>
                    {listeningQuestions[listeningIndex].translation}
                  </p>
                </div>
              )}

              <button
                className="practice-start-button"
                onClick={nextListeningQuestion}
              >
                {listeningIndex + 1 === listeningQuestions.length
                  ? "See Results"
                  : "Next Question →"}
              </button>
            </div>
          )}
        </section>
      )}
  </main>
)}

      {/* =====================================================
          VOCABULARY PAGE
      ===================================================== */}

      {page === "vocabulary" && (

        <main className="container vocabulary-page">

          <section className="vocabulary-header">

            <div>

              <p className="eyebrow">
                YOUR WORDS
              </p>

              <h1>
                Vocabulary
              </h1>

              <p className="vocabulary-subtitle">
                Words you've saved while learning.
              </p>

            </div>

            <div className="vocabulary-count">

              <strong>
                {
                  vocabulary.filter(
                    isValidQuizWord
                  ).length
                }
              </strong>

              <span>
                reviewable words
              </span>

            </div>

          </section>

          <div className="vocabulary-search">

            <input
              type="text"
              placeholder="Search words, reading, romaji or meaning..."
              value={search}
              onChange={(event) =>
                setSearch(
                  event.target.value
                )
              }
            />

          </div>

          {vocabularyLoading && (

            <div className="vocabulary-message">
              Loading vocabulary...
            </div>

          )}

          {vocabularyError && (

            <div className="vocabulary-message error-message">
              {vocabularyError}
            </div>

          )}

          {!vocabularyLoading &&
            vocabulary.length === 0 && (

              <div className="empty-vocabulary">

                <div className="empty-icon">
                  📚
                </div>

                <h2>
                  No saved words yet
                </h2>

                <p>
                  Analyze a Japanese sentence and
                  save words to build your vocabulary.
                </p>

                <button
                  className="practice-start-button"
                  onClick={openAnalyzer}
                >
                  Analyze a sentence →
                </button>

              </div>

            )}

          {!vocabularyLoading &&
            filteredVocabulary.length > 0 && (

              <div className="vocabulary-grid">

                {filteredVocabulary.map(
                  (word) => (

                    <div
                      className="vocabulary-card"
                      key={word.id}
                      onClick={() =>
                        setSelectedWord(
                          word
                        )
                      }
                    >

                      <div className="saved-word">
                        {word.word}
                      </div>

                      <div className="saved-reading">
                        {word.reading}
                      </div>

                      <div className="saved-romaji">
                        {word.romaji}
                      </div>

                      <div className="saved-meaning">
                        {word.meaning}
                      </div>

                      {word.role && (
                        <div className="saved-role">
                          {word.role}
                        </div>
                      )}

                      {word.reviewable === 1 && (
                        <div className="saved-role">
                          Reviewable
                        </div>
                      )}

                    </div>

                  )
                )}

              </div>

            )}

        </main>

      )}

      {/* =====================================================
          PRACTICE PAGE
      ===================================================== */}

      {page === "practice" && (

        <main className="container practice-page">

          <section className="practice-header">

            <p className="eyebrow">
              PRACTICE
            </p>

            <h1>
              Practice your vocabulary
            </h1>

            <p className="practice-subtitle">
              Review your saved words and test yourself.
            </p>

          </section>

          {/* PRACTICE START */}

          {!practiceStarted &&
            !quizStarted && (

              <div className="practice-start-card">

                <div className="practice-icon">
                  🧠
                </div>

                <h2>
                  Ready to practice?
                </h2>

                <p>
                  Choose how you want to practice
                  your saved vocabulary.
                </p>

                <div className="practice-start-actions">

                  <button
                    className="practice-start-button"
                    onClick={startPractice}
                    disabled={
                      vocabulary.filter(
                        isValidQuizWord
                      ).length === 0
                    }
                  >
                    Flashcards →
                  </button>

                  <button
                    className="practice-start-button quiz-start-button"
                    onClick={startQuiz}
                    disabled={
                      vocabulary.filter(
                        isValidQuizWord
                      ).length < 4
                    }
                  >
                    Multiple Choice Quiz →
                  </button>

                </div>

                {vocabulary.filter(
                  isValidQuizWord
                ).length < 4 && (

                  <p className="practice-warning">
                    Save at least 4 reviewable
                    words with meanings to use
                    Multiple Choice Quiz.
                  </p>

                )}

              </div>

            )}

          {/* FLASHCARDS */}

          {practiceStarted &&
            practiceIndex <
              vocabulary.length && (

              <div className="practice-card">

                <div className="practice-progress">
                  Word {practiceIndex + 1} of{" "}
                  {vocabulary.length}
                </div>

                <div className="practice-word">
                  {
                    vocabulary[
                      practiceIndex
                    ].word
                  }
                </div>

                <div className="practice-reading">
                  {
                    vocabulary[
                      practiceIndex
                    ].reading
                  }
                </div>

                <div className="practice-romaji">
                  {
                    vocabulary[
                      practiceIndex
                    ].romaji
                  }
                </div>

                {!showAnswer && (

                  <button
                    className="show-answer-button"
                    onClick={() =>
                      setShowAnswer(true)
                    }
                  >
                    Show Answer
                  </button>

                )}

                {showAnswer && (

                  <>

                    <div className="practice-answer">
                      {
                        vocabulary[
                          practiceIndex
                        ].meaning
                      }
                    </div>

                    <div className="practice-buttons">

                      <button
                        className="didnt-know"
                        onClick={() =>
                          answerPractice(false)
                        }
                      >
                        I didn't know
                      </button>

                      <button
                        className="knew"
                        onClick={() =>
                          answerPractice(true)
                        }
                      >
                        I knew it ✓
                      </button>

                    </div>

                  </>

                )}

              </div>

            )}

          {/* FLASHCARD COMPLETE */}

          {practiceStarted &&
            practiceIndex >=
              vocabulary.length && (

              <div className="practice-complete">

                <div className="practice-complete-icon">
                  🎉
                </div>

                <h2>
                  Practice complete!
                </h2>

                <p>
                  You knew{" "}
                  <strong>
                    {practiceScore}
                  </strong>{" "}
                  out of{" "}
                  <strong>
                    {vocabulary.length}
                  </strong>{" "}
                  words.
                </p>

                <button
                  className="practice-start-button"
                  onClick={startPractice}
                >
                  Practice Again
                </button>

              </div>

            )}

          {/* QUIZ */}

          {quizStarted &&
            quizIndex <
              quizWords.length && (

              <div className="quiz-card">

                <div className="quiz-top">

                  <span>
                    Question {quizIndex + 1} /{" "}
                    {quizWords.length}
                  </span>

                  <span>
                    Score: {quizScore}
                  </span>

                </div>

                <div className="quiz-word">
                  {
                    quizWords[
                      quizIndex
                    ].word
                  }
                </div>

                <div className="quiz-reading">
                  {
                    quizWords[
                      quizIndex
                    ].reading
                  }
                </div>

                <div className="quiz-romaji">
                  {
                    quizWords[
                      quizIndex
                    ].romaji
                  }
                </div>

                <p className="quiz-question">
                  What does this mean?
                </p>

                <div className="quiz-options">

                  {quizOptions.map(
                    (option) => {

                      const isSelected =
                        selectedAnswer?.id ===
                        option.id;

                      const isCorrect =
                        option.id ===
                        quizWords[
                          quizIndex
                        ].id;

                      let className =
                        "quiz-option";

                      if (selectedAnswer) {

                        if (isCorrect) {
                          className +=
                            " correct";
                        } else if (
                          isSelected
                        ) {
                          className +=
                            " incorrect";
                        }

                      }

                      return (

                        <button
                          key={option.id}
                          className={
                            className
                          }
                          onClick={() =>
                            selectQuizAnswer(
                              option
                            )
                          }
                        >
                          {option.meaning}
                        </button>

                      );

                    }
                  )}

                </div>

                {selectedAnswer && (

                  <>

                    <div className="quiz-feedback">

                      {
                        selectedAnswer.id ===
                        quizWords[
                          quizIndex
                        ].id
                          ? "✓ Correct!"
                          : `✗ Correct answer: ${
                              quizWords[
                                quizIndex
                              ].meaning
                            }`
                      }

                    </div>

                    <button
                      className="next-question-button"
                      onClick={
                        nextQuizQuestion
                      }
                    >
                      {
                        quizIndex + 1 >=
                        quizWords.length
                          ? "See Results →"
                          : "Next Question →"
                      }
                    </button>

                  </>

                )}

              </div>

            )}

          {/* QUIZ COMPLETE */}

          {quizStarted &&
            quizIndex >=
              quizWords.length && (

              <div className="quiz-complete">

                <div className="practice-complete-icon">
                  🎉
                </div>

                <h2>
                  Quiz Complete!
                </h2>

                <div className="final-score">
                  {quizScore} /{" "}
                  {quizWords.length}
                </div>

                <p>
                  {Math.round(
                    (quizScore /
                      quizWords.length) *
                      100
                  )}
                  % correct
                </p>

                <button
                  className="practice-start-button"
                  onClick={startQuiz}
                >
                  Try Again
                </button>

              </div>

            )}

        </main>

      )}

      {/* =====================================================
          PROGRESS PAGE
      ===================================================== */}

      {page === "progress" && (

        <main className="container progress-page">

          <section className="progress-header">

            <p className="eyebrow">
              YOUR LEARNING
            </p>

            <h1>
              Progress
            </h1>

            <p className="progress-subtitle">
              Track your vocabulary and quiz performance.
            </p>

          </section>

          <div className="progress-stats">

            <div className="progress-stat-card">

              <span className="progress-stat-value">
                {
                  vocabulary.filter(
                    isValidQuizWord
                  ).length
                }
              </span>

              <span className="progress-stat-label">
                Reviewable Words
              </span>

            </div>

            <div className="progress-stat-card">

              <span className="progress-stat-value">
                {quizHistory.length}
              </span>

              <span className="progress-stat-label">
                Quizzes Taken
              </span>

            </div>

            <div className="progress-stat-card">

              <span className="progress-stat-value">
                {totalCorrectAnswers}
              </span>

              <span className="progress-stat-label">
                Correct Answers
              </span>

            </div>

            <div className="progress-stat-card">

              <span className="progress-stat-value">
                {overallAccuracy}%
              </span>

              <span className="progress-stat-label">
                Accuracy
              </span>

            </div>

          </div>

          <section className="progress-card">

            <div className="progress-card-header">

              <div>

                <div className="result-label">
                  QUIZ PERFORMANCE
                </div>

                <h2>
                  Overall accuracy
                </h2>

              </div>

              <strong>
                {overallAccuracy}%
              </strong>

            </div>

            <div className="progress-bar">

              <div
                className="progress-bar-fill"
                style={{
                  width: `${Math.min(
                    overallAccuracy,
                    100
                  )}%`,
                }}
              />

            </div>

            {quizHistory.length === 0 && (

              <p className="progress-empty">
                Complete your first quiz to start
                tracking your performance.
              </p>

            )}

          </section>

          <section className="progress-card">

            <div className="result-label">
              QUIZ HISTORY
            </div>

            {quizHistory.length === 0 ? (

              <div className="progress-empty">
                No quizzes completed yet.
              </div>

            ) : (

              <div className="quiz-history">

                {quizHistory.map(
                  (quiz, index) => (

                    <div
                      className="quiz-history-item"
                      key={quiz.id}
                    >

                      <div>

                        <strong>
                          Quiz{" "}
                          {quizHistory.length -
                            index}
                        </strong>

                        <span>
                          {quiz.date}
                        </span>

                      </div>

                      <div className="history-score">

                        <strong>
                          {quiz.score} /{" "}
                          {quiz.total}
                        </strong>

                        <span>
                          {quiz.percentage}%
                        </span>

                      </div>

                    </div>

                  )
                )}

              </div>

            )}

          </section>

          {quizHistory.length > 0 && (

            <div className="progress-message">

              {overallAccuracy >= 90
                ? "🔥 Excellent! You're mastering your vocabulary."
                : overallAccuracy >= 70
                ? "💪 Great progress! Keep practicing."
                : "📚 Keep practicing. Your accuracy will improve."}

            </div>

          )}

        </main>

      )}

      {/* =====================================================
          WORD MODAL
      ===================================================== */}

      {selectedWord && (

        <div
          className="modal-overlay"
          onClick={() =>
            setSelectedWord(null)
          }
        >

          <div
            className="word-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >

            <button
              className="modal-close"
              onClick={() =>
                setSelectedWord(null)
              }
            >
              ×
            </button>

            <div className="modal-word">
              {selectedWord.word}
            </div>

            {selectedWord.reading && (

              <div className="modal-reading">
                {selectedWord.reading}
              </div>

            )}

            {selectedWord.romaji && (

              <div className="modal-romaji">
                {selectedWord.romaji}
              </div>

            )}

            {selectedWord.meaning && (

              <div className="modal-meaning">
                {selectedWord.meaning}
              </div>

            )}

            {selectedWord.part_of_speech && (

              <div className="modal-detail">

                <strong>
                  Part of speech:
                </strong>

                <span>
                  {
                    selectedWord.part_of_speech
                  }
                </span>

              </div>

            )}

            {selectedWord.role && (

              <div className="modal-detail">

                <strong>
                  Role:
                </strong>

                <span>
                  {selectedWord.role}
                </span>

              </div>

            )}

            {page === "analyze" && (

              <>

                <button
                  className="save-word-button"
                  onClick={saveWord}
                  disabled={savingWord}
                >
                  {savingWord
                    ? "Saving..."
                    : "Save to Vocabulary"}
                </button>

                {saveMessage && (

                  <div className="save-message">
                    {saveMessage}
                  </div>

                )}

              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;