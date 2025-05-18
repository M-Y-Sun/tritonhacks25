from transformers import pipeline
import argparse

# Define the confidence threshold
TAU = 0.8

def classify_emergency(text):
    # Initialize the classifier
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

    # Define candidate labels for emergency classification
    candidate_labels = ["medical emergency", "fire emergency", "police emergency",
                       "traffic accident", "non-emergency"]

    # Perform multi-label classification
    result = classifier(text, candidate_labels, multi_label=True)
    
    scores = result['scores']
    labels = result['labels']
    
    p_max = 0.0
    i_max = -1

    if scores: # Check if scores list is not empty
        p_max = max(scores)
        i_max = scores.index(p_max)

    if p_max >= TAU and i_max != -1:
        prediction = labels[i_max]
        confidence = p_max
    else:
        prediction = "uncertain"
        confidence = p_max # Still return the max probability found, even if uncertain

    return prediction, confidence

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Classify emergency text')
    parser.add_argument('text', type=str, help='The text to classify')

    # Parse arguments
    args = parser.parse_args()

    # Classify the text
    classification, confidence = classify_emergency(args.text)

    # Print results
    print(f"\nClassification: {classification}")
    if classification == "uncertain":
        print(f"Highest Confidence Score: {confidence:.2%}")
    else:
        print(f"Confidence: {confidence:.2%}")

if __name__ == "__main__":
    main()
