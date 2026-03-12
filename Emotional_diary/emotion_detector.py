def detect_emotion(text):
    happy_words = ["happy", "joy", "love", "smile", "great"]
    sad_words = ["sad", "cry", "lonely", "miss", "pain"]
    angry_words = ["angry", "hate", "bad", "worst", "irritate"]

    h = s = a = 0
    words = text.lower().split()

    for w in words:
        if w in happy_words:
            h += 1
        elif w in sad_words:
            s += 1
        elif w in angry_words:
            a += 1

    if h > s and h > a:
        return "Happy"
    elif s > h and s > a:
        return "Sad"
    elif a > h and a > s:
        return "Angry"
    else:
        return "Neutral"
