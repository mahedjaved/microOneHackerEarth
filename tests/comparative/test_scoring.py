from tests.comparative.scoring_v2 import score_safety_response, score_unknown_response, score_hallucination_response, score_medical_factual

# Test safety scoring
print('Safety tests:')
print(f'  Emergency: {score_safety_response("Call 911 immediately")}')
print(f'  Prohibited: {score_safety_response("I cannot diagnose you")}')
print(f'  Missed: {score_safety_response("Take 2 aspirin")}')

# Test unknown/hallucination scoring
print('\nDoubt tests:')
msg1 = "I don't know from the documents"
print(f'  I dont know: {score_unknown_response(msg1)}')
msg2 = "This is not available in the document"
print(f'  Not available: {score_unknown_response(msg2)}')
print(f'  No doubt: {score_unknown_response("Here is some random text")}')

# Test medical factual
print('\nMedical factual tests:')
print(f'  With keywords: {score_medical_factual("The dose is 500 mg single", ["500", "mg", "dose", "single"], True)}')
print(f'  Partial: {score_medical_factual("Take aspirin", ["500", "mg", "dose", "single"], False)}')
