import pandas as pd
import pickle
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ---------- NLTK SETUP ----------
try:
    stop_words = set(stopwords.words('english'))
except:
    nltk.download('stopwords')
    nltk.download('wordnet')
    stop_words = set(stopwords.words('english'))

lemmatizer = WordNetLemmatizer()

# ---------- TEXT PREPROCESSING ----------
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)

    words = text.split()
    words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]

    return " ".join(words)

# ---------- DATASET ----------
data = {
    "text": [

        # HAPPY (50)
        "I feel amazing today","Today is wonderful","I feel very happy",
        "Life is beautiful","I achieved my goal","I feel proud today",
        "Everything is going great","I love spending time with friends",
        "I feel joyful","I feel fantastic","Today made me smile",
        "I am in a good mood","This is a lovely day","I feel satisfied",
        "I am enjoying my life","I feel grateful","I feel blessed",
        "Today was awesome","I feel positive","I am feeling great",
        "I feel cheerful","I am excited about life","I feel content",
        "I am feeling relaxed","I am very delighted","Today feels good",
        "I am feeling energetic","I feel optimistic","I feel wonderful",
        "Everything feels perfect","I feel very lucky","Today is amazing",
        "I feel so happy","I feel relaxed and happy","I feel good today",
        "I feel joyful inside","My day went well","I feel confident",
        "I feel peaceful","I am happy with my progress",
        "Life is treating me well","I feel proud of my work",
        "I feel calm and happy","My heart feels light",
        "I feel encouraged","I am satisfied today",
        "Today was fantastic","I feel inspired",
        "I feel motivated","Everything feels bright",

        # SAD (50)
        "I feel very sad","Today was terrible","I feel lonely",
        "Nothing is going right","I feel down today","I feel hopeless",
        "I am emotionally tired","I feel heartbroken","I feel depressed",
        "I feel disappointed","Life feels hard","I miss someone",
        "I feel like crying","I feel miserable","I feel empty",
        "I feel abandoned","I feel hurt","I feel ignored",
        "I feel weak emotionally","Today feels dark","I feel low",
        "I feel unhappy","I feel broken","I feel discouraged",
        "I feel helpless","I feel lost","I feel upset",
        "My heart feels heavy","I feel alone","I feel gloomy",
        "I feel tired of everything","I feel pain inside",
        "I feel disappointed in life","I feel drained",
        "Nothing feels good","I feel emotionally weak",
        "I feel like giving up","Today is a bad day",
        "I feel sorrow","I feel regret","I feel grief",
        "I feel defeated","I feel stressed and sad",
        "I feel forgotten","I feel isolated",
        "I feel unloved","I feel hopeless today",
        "I feel emotionally lost","My mood is very low",

        # ANGRY (50)
        "I am very angry","This made me furious","I feel frustrated",
        "I hate this situation","I feel irritated","I lost my temper",
        "I am annoyed","This is unacceptable","I feel rage",
        "I cannot tolerate this","I feel extremely angry",
        "I feel aggressive","I feel mad","I feel furious",
        "I feel irritated today","I feel outraged",
        "This situation makes me angry","I feel offended",
        "I feel upset and angry","I feel boiling inside",
        "I feel provoked","I feel heated","I feel hostile",
        "I feel bitter","I feel annoyed today","I feel resentment",
        "I feel anger building up","I feel like shouting",
        "This makes me mad","I feel intense anger",
        "I feel very irritated","I feel fed up",
        "I feel angry about this","I feel rage inside",
        "This is very frustrating","I feel explosive",
        "I feel impatient","I feel extremely annoyed",
        "I feel hatred","I feel resentment today",
        "This situation is infuriating","I feel tension",
        "I feel aggressive energy","I feel anger rising",
        "I feel outraged today","I feel hostility",
        "I feel mad at everything","I feel burning anger",

        # FEAR (50)
        "I feel scared","I feel nervous","I am worried",
        "I feel anxious","I am afraid of failing",
        "I feel stressed about exams","I fear the worst",
        "I feel panic","Something feels wrong",
        "I feel uncomfortable","I feel tense",
        "I feel uneasy","I feel threatened",
        "I feel afraid today","I feel worried about tomorrow",
        "I feel fear inside","I feel insecure",
        "I feel anxious today","I feel stressed",
        "I feel uncertain","I feel scared about the future",
        "I feel restless","I feel afraid of mistakes",
        "I feel pressure","I feel panic inside",
        "I feel frightened","I feel uneasy today",
        "I feel worried about life","I feel shaky",
        "I feel afraid of problems","I feel nervous today",
        "I feel fear rising","I feel uncertain about tomorrow",
        "I feel stressed out","I feel overwhelmed",
        "I feel scared of failure","I feel worried about results",
        "I feel uncomfortable today","I feel afraid of changes",
        "I feel tense today","I feel threatened by challenges",
        "I feel fearful","I feel panic about exams",
        "I feel worried constantly","I feel anxious about future",
        "I feel scared inside","I feel unstable emotionally",

        # NEUTRAL (50)
        "It was an ordinary day","Nothing special happened",
        "I went to work","I completed my tasks",
        "Today was normal","I attended classes",
        "I had lunch","I read a book",
        "I watched TV","Just another regular day",
        "I followed my routine","It was a typical day",
        "I did my daily work","Nothing unusual today",
        "I had a normal schedule","It was a calm day",
        "I completed routine tasks","Today felt average",
        "It was a quiet day","I finished my work",
        "I studied today","I attended meetings",
        "I did household work","I relaxed at home",
        "I spent time online","I walked outside",
        "I had dinner","I watched some videos",
        "I checked emails","I cleaned my room",
        "I organized my notes","I worked on my tasks",
        "I finished assignments","I attended lectures",
        "I did some reading","I took a short walk",
        "I listened to music","I spent time alone",
        "I followed my schedule","I rested at home",
        "I had tea","I checked my phone",
        "I completed routine work","I attended online classes",
        "I relaxed quietly","I finished chores",
        "I followed my plan","It was a simple day",
        "Today was just normal"
    ],

    "emotion": (
        ["Happy"]*50 +
        ["Sad"]*50 +
        ["Angry"]*50 +
        ["Fear"]*50 +
        ["Neutral"]*50
    )
}

df = pd.DataFrame(data)

# ---------- PREPROCESS ----------
df["text"] = df["text"].apply(preprocess_text)

# ---------- VECTORIZATION ----------
vectorizer = TfidfVectorizer(
    ngram_range=(1,2),
    max_features=3000,
    min_df=1
)

X = vectorizer.fit_transform(df["text"])
y = df["emotion"]

# ---------- TRAIN / TEST SPLIT ----------
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42
)

# ---------- MODEL ----------
model = LogisticRegression(
    max_iter=2000,
    class_weight='balanced'
)

model.fit(X_train, y_train)

# ---------- PREDICT ----------
predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("Model Accuracy:", round(accuracy*100,2), "%")

# ---------- SAVE MODEL ----------
with open("emotion_model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("🔥 Advanced Emotion Model trained and saved successfully!")