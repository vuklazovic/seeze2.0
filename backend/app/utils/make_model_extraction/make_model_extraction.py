import spacy
import re
from spacy.matcher import Matcher
from spacy.tokens import Span
from spacy.language import Language
import json
from collections import Counter
from itertools import combinations
import time
import math
from collections import defaultdict



def load_car_data(file_path):
    with open(file_path, encoding='utf-8-sig') as file:
        data = json.load(file)
    
    car_data = {}
    
    for make, models in data.items():
        make_data = {}
        for model, trims in models.items():
            make_data[model] = list(trims.keys())
        car_data[make] = make_data
    
    return car_data

# Dictionary that maps trim aliases to an original trim value. 
# For example, e300 and e 300 should map to the same car. 
# IMPORTANT: Trims have to belong to the same model class! 
# e300 and e 300 are both members of "e-class"

def load_lookup_dict(file_path):
    with open(file_path, 'r') as infile:
        lookup_dict = json.load(infile)
    
    return lookup_dict

# For runnging test
# car_data_path = r'./jsons/MakeModelTrimYear_HARCDODED_GENERALIZED.json'
# model_lookup_dict_path = r'./jsons/model_lookup_dict.json'
# trim_lookup_dict_path = r'./jsons/trim_lookup_dict.json'
# For production
car_data_path = r'./app/utils/make_model_extraction/jsons/MakeModelTrimYear_HARCDODED_GENERALIZED.json'
model_lookup_dict_path = r'./app/utils/make_model_extraction/jsons/model_lookup_dict.json'
trim_lookup_dict_path = r'./app/utils/make_model_extraction/jsons/trim_lookup_dict.json'

# print(f"NOTE: Using car data filepath {car_data_path}")
car_data = load_car_data(car_data_path)
model_lookup_dict = load_lookup_dict(model_lookup_dict_path)
trim_lookup_dict = load_lookup_dict(trim_lookup_dict_path)


car_makes = list(car_data.keys())
########################
# SASHA's CODE: Hard-Coding Make Aliases into our extractor
car_makes.append("mercedes")    # Mercedes-Benz
car_makes.append("chevy")       # Chevrolet
car_makes.append("vw")          # Volkswagen
car_makes.append("rr")          # Rolls Royce
#car_makes.append("benz")        # Mercedes-Benz
#######################
all_models = [model for models in car_data.values() for model in models.keys()]
all_trims = [trim for models in car_data.values() for trims in models.values() for trim in trims]

nlp = spacy.load('en_core_web_sm')


@Language.component("add_car_entities")
def add_car_entities(doc):
    matcher = Matcher(nlp.vocab)

    ## DEBUG
    car_makes.append("am general")
    pattern_make = [{"LOWER": {"IN": [make.lower() for make in car_makes]}}]
    matcher.add("CAR_MAKE", [pattern_make])

    matches = matcher(doc)
    spans = [Span(doc, start, end, label=nlp.vocab.strings[match_id]) for match_id, start, end in matches]
    spans = spacy.util.filter_spans(spans)
    doc.ents = spans

    return doc


nlp.add_pipe("add_car_entities", before="ner")

#(O(1) time complexity, possibly lesser accuracy)
# def get_closest_match(text, options):
#     text_set = set(text.lower().split())
#     print(text_set)
#     max_similarity = 0
#     best_match = None

#     for option in options:
#         print(option)
#         option_set = set(option.lower().split())
#         similarity = len(text_set & option_set) / len(text_set | option_set)
        
#         if similarity > max_similarity:
#             max_similarity = similarity
#             best_match = option
#     if max_similarity > 0.01:
#         return best_match
#     return None
    
#     #return best_match   


# returns list of key values in dictionary which map to the same value. 
# Takes dictionary (d) as argument and the target value, and returns a list of keys which map to this target value
def keys_for_value(d, target_value):
    return [key for key, value in d.items() if value == target_value]

# remove sublist of elements from a larger list
def remove_sublist_elements(large_list, sublist):
    sublist_set = set(sublist)
    return [item for item in large_list if item not in sublist_set]

def split_string_on_letter_number_transition(s):
    # Use a regex to split the string at letter-number, number-letter transitions, or spaces
    text=re.split(r'(?<=[a-zA-Z])(?=\d)|(?<=\d)(?=[a-zA-Z])|\s+', s)
    nospace=[]
    for t in text:
        t.replace(" ", "")
        nospace.append(t)
    return nospace


def sequence_similarity(option, substring):
    option_clean=re.sub(r'[^a-zA-Z0-9\s#+\-\.!]', ' ', option)
    option_clean = re.sub(r'[-/]', ' ', option_clean)
    option_clean = option_clean.lower()
    substring = substring.lower()
    
    m, n = len(option_clean), len(substring)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if option_clean[i-1] == substring[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])

    LCS_score = dp[m][n] / max(m, n)
    #LCS_score = dp[m][n] 

    # print(f"LCS between {option_clean}, {substring} is: {LCS_score}")
    # print(LCS_score, option)
    return LCS_score

def get_closest_match(text, options, similarity_threshold=0.75):
    all_substrings = set()
    split = text.split(" ")

    for i in range(1, min(6, len(split) + 1)):
        for combo in combinations(split, i):
            all_substrings.add(' '.join(combo).lower())
            all_substrings.add(''.join(combo).lower())

    text = re.sub(r'[^a-zA-Z0-9\s#+\-\.!]', ' ', text)
    text = re.sub(r'[-/]', ' ', text)
    
    words = text.lower().split()
    max_similarity = 0
    best_matches = []
    
    for i in range(1, min(6, len(words) + 1)):
        for combo in combinations(words, i):
            all_substrings.add(' '.join(combo).lower())
            all_substrings.add(''.join(combo).lower())
    
    ## all_substrings.append(instances where)
    num_letter_splits = split_string_on_letter_number_transition(text)
    #print(num_letter_splits)

    for i in range(1, min(6, len(num_letter_splits) + 1)):
        for combo in combinations(num_letter_splits, i):
            all_substrings.add(' '.join(combo).lower())
            all_substrings.add(''.join(combo).lower())
    
    # Instead of doing substrings, compare similarity between (text, option), and return which one has highest
    #print("all substrings", all_substrings)
    for substring in all_substrings:
        for option in options:
            option_clean=re.sub(r'[^a-zA-Z0-9\s#+\-\.!]', ' ', option)
            option_clean = re.sub(r'[-/]', ' ', option_clean)
            option_lower = option_clean.lower()
            option_chars = Counter(option_lower)
            substring_chars = Counter(substring)

            intersection = sum((option_chars & substring_chars).values())
            union = sum((option_chars | substring_chars).values())

            similarity = intersection / union if union > 0 else 0

            if similarity > max_similarity:
                max_similarity = similarity
                best_matches = [(option, substring, similarity)]

            # elif similarity == max_similarity or similarity > max_similarity*0.85:
            elif similarity == max_similarity:
                best_matches.append((option, substring, similarity))

    if max_similarity >= similarity_threshold:
        if len(best_matches) > 1:
            # print("best matches", best_matches)
            best_match = max(best_matches, key=lambda x: (sequence_similarity(x[0], x[1]), len(x[0])))
            return best_match[0], best_match[2]
        else:
            # print(best_matches[0][0], best_matches[0][2])
            return best_matches[0][0], best_matches[0][2]
    else:
        return None, 0

def extract_info(listing, similarity_threshold=0.75):
    #print(f"NOTE: Using similarity threshold of {similarity_threshold}")
    listing = listing.lower() 

    doc = nlp(listing)

    make = model = trim = year = mileage = None

    if " g wagon" in listing.lower():            # Handling G wagon exception manually
        
        found_make = "mercedes-benz"
        found_model = "g-class"
        found_trim = extract_trim_only(listing, found_make, found_model, similarity_threshold=0.75)[0]
        if found_trim == None:
            found_trim = " "

        return_dict =  {
        'extracted_make': found_make,
        'extracted_model': found_model,
        'extracted_trim': found_trim
        }

        return return_dict
    
    for ent in doc.ents:
        if ent.label_ == "CAR_MAKE":
            make = ent.text
            break 

    if not make:
        make, _ = get_closest_match(listing, car_makes, similarity_threshold)
    if not make:
        all_models = [model for make_models in car_data.values() for model in make_models]
        model, _ = get_closest_match(listing, all_models, similarity_threshold)
        if model:
            for m, models in car_data.items():
                if model.lower() in [mod.lower() for mod in models]:
                    make = m
                    break

    ## DEBUG: Remove make, model, or trim from listing once matched
    if make != None:
        listing = listing.replace(make, '')
        listing = listing.lstrip()
        doc = nlp(listing)

    # SASHA'S CODE: Assigning original makes to aliases 
    if make != None and make.lower() == "mercedes":
        make = "mercedes-benz"
    
    if make != None and make.lower() == "vw":
        make = "volkswagen"
    
    if make != None and make.lower() == "rr":
        make = "rolls-royce"

    if make != None and make.lower() == "chevy":
        make = "chevrolet"

    if make:
        models = list(car_data[make.lower()].keys())
        pattern_model = [{"LOWER": {"IN": [model.lower() for model in models]}}]

        matcher = Matcher(nlp.vocab)
        matcher.add("CAR_MODEL", [pattern_model])

        matches = matcher(doc)
        spans = [Span(doc, start, end, label="CAR_MODEL") for match_id, start, end in matches]
        spans = spacy.util.filter_spans(spans)
        doc.ents = spans

        
        model, _ = get_closest_match(listing, models, similarity_threshold)
        

        if not model:
            for ent in doc.ents:
                if ent.label_ == "CAR_MODEL":
                    model = ent.text
                    break

        if not model:
            model_to_model_no_space = {model.replace(" ", ""): model for model in models}
            all_models_no_space = list(model_to_model_no_space.keys())
            model_no_space, _ = get_closest_match(listing, all_models_no_space, similarity_threshold)

            if model_no_space:
                model = model_to_model_no_space[model_no_space]

    if not model and make:
        all_trims = []
        for model_trims in car_data[make.lower()].values():
            all_trims.extend(model_trims)
        
        pattern_trim = [{"LOWER": {"IN": [trim.lower().replace(" ", "") for trim in all_trims]}}]
        
        matcher = Matcher(nlp.vocab)
        matcher.add("CAR_TRIM", [pattern_trim])
        
        matches = matcher(doc)
        spans = [Span(doc, start, end, label="CAR_TRIM") for match_id, start, end in matches]
        spans = spacy.util.filter_spans(spans)
        doc.ents = spans
        trim, _ = get_closest_match(listing, all_trims, similarity_threshold)
        
        if not trim:   
            for ent in doc.ents:
                if ent.label_ == "CAR_TRIM":
                    #trim = ent.text
                    trim, _ = get_closest_match(ent.text, all_trims, similarity_threshold)
                    break

        if not trim:
            trim_to_trim_no_space = {trim.replace(" ", ""): trim for trim in all_trims}
            all_trims_no_space = list(trim_to_trim_no_space.keys())
            trim_no_space, _ = get_closest_match(listing, all_trims_no_space, similarity_threshold)

            if trim_no_space:
                trim = trim_to_trim_no_space[trim_no_space]

        if trim and trim in all_trims:
            for model_name, trims in car_data[make.lower()].items():
                if trim.replace(" ", "") in [t.replace(" ", "") for t in trims]:
                    model = model_name
                    break
        

    elif model:
        if make != "mercedes-benz":         # Can't remove make for mercedes because of sl, gls, s, ...
            listing = listing.replace(model, "")
            listing = listing.lstrip()
            doc = nlp(listing)
        
        trims = car_data[make.lower()][model.lower()]
        pattern_trim = [{"LOWER": {"IN": [trim.lower() for trim in trims]}}]

        matcher = Matcher(nlp.vocab)
        matcher.add("CAR_TRIM", [pattern_trim])

        matches = matcher(doc)
        spans = [Span(doc, start, end, label="CAR_TRIM") for match_id, start, end in matches]
        spans = spacy.util.filter_spans(spans)
        doc.ents = spans

        trim, _ = get_closest_match(listing, trims, similarity_threshold)

        if not trim:
            for ent in doc.ents:
                if ent.label_ == "CAR_TRIM":
                    trim = ent.text
                    break

        if not trim:
            trim_to_trim_no_space = {trim.replace(" ", ""): trim for trim in trims}
            all_trims_no_space = list(trim_to_trim_no_space.keys())
            trim_no_space, _ = get_closest_match(listing, all_trims_no_space, similarity_threshold)

            if trim_no_space:
                trim = trim_to_trim_no_space[trim_no_space]

    if not model:
        all_models = []
        for make_data in car_data.values():
            all_models.extend(make_data.keys())

        pattern_model = [{"LOWER": {"IN": [model.lower().replace(" ", "") for model in all_models]}}]
        matcher = Matcher(nlp.vocab)
        matcher.add("CAR_MODEL", [pattern_model])
        matches = matcher(doc)
        spans = [Span(doc, start, end, label="CAR_MODEL") for match_id, start, end in matches]
        spans = spacy.util.filter_spans(spans)
        doc.ents = spans

        found_model, _ = get_closest_match(listing, all_models, similarity_threshold)

        if not found_model:
            for ent in doc.ents:
                if ent.label_ == "CAR_MODEL":
                    found_model = ent.text
                    break

        if not found_model:
            model_to_model_no_space = {model.replace(" ", ""): model for model in all_models}
            all_models_no_space = list(model_to_model_no_space.keys())
            model_no_space, _ = get_closest_match(listing, all_models_no_space, similarity_threshold)

            if model_no_space:
                found_model = model_to_model_no_space[model_no_space]

        if found_model:
            model = found_model  # Only set model if it wasn't already set
            if not make:
                for m, models in car_data.items():
                    if model.lower() in [m.lower() for m in models]:
                        make = m
                        break

        if not model:
            all_trims = []
            for make_data in car_data.values():
                for model_data in make_data.values():
                    all_trims.extend(model_data)
            
            pattern_trim = [{"LOWER": {"IN": [trim.lower().replace(" ", "") for trim in all_trims]}}]
            matcher = Matcher(nlp.vocab)
            matcher.add("CAR_TRIM", [pattern_trim])
            matches = matcher(doc)
            spans = [Span(doc, start, end, label="CAR_TRIM") for match_id, start, end in matches]
            spans = spacy.util.filter_spans(spans)
            doc.ents = spans

            found_trim, _ = get_closest_match(listing, all_trims, similarity_threshold)

            if not found_trim:
                for ent in doc.ents:
                    if ent.label_ == "CAR_TRIM":
                        found_trim = ent.text
                        break

            if not found_trim:
                trim_to_trim_no_space = {trim.replace(" ", ""): trim for trim in all_trims}
                all_trims_no_space = list(trim_to_trim_no_space.keys())
                trim_no_space, _ = get_closest_match(listing, all_trims_no_space, similarity_threshold)

                if trim_no_space:
                    found_trim = trim_to_trim_no_space[trim_no_space]

            if found_trim:
                trim = found_trim  # Only set trim if it wasn't already set
                # Don't overwrite existing make or model based on trim

    if trim and not model:
        for make_name, models in car_data.items():
            for model_name, trims in models.items():
                if trim.lower() in [t.lower() for t in trims]:
                    if not model:
                        model = model_name
                    if not make:
                        make = make_name
                    break

    if model and not make:
        for make_name, models in car_data.items():
            if model.lower() in [m.lower() for m in models.keys()]:
                make = make_name
                break
            
    
    if make and model:
        if model.lower() not in car_data[make.lower()]:
            model = None
            trim = None
        elif trim:
            if trim.lower() not in [t.lower() for t in car_data[make.lower()][model.lower()]]:
                trim = None
        else:
            trims = car_data[make.lower()][model.lower()]
            found_trim, _ = get_closest_match(listing, trims, similarity_threshold)
            if found_trim:
                trim = found_trim

    # year_match = re.search(r'\b(?:19|20)\d{2}\b(?!\s*(?:miles|mi))', listing)
    # if year_match:
    #     year = int(year_match.group(0))

    # mileage_pattern = r'\b(\d{1,3}(?:,\d{3})*|\d+(?:\.\d+)?)\s*(?:miles|mi\.?|k miles|k mi\.?|k|km)\b'
    # mileage_match = re.search(mileage_pattern, listing, re.IGNORECASE)
    # if mileage_match:
    #     mileage_str = mileage_match.group(1).replace(',', '')
    #     mileage = int(float(mileage_str) * (1000 if 'k' in mileage_match.group(0).lower() else 1))

    # Basically, if we extract a trim, see if we can extract a more specific trim using remaining words in the listing 
    # Example: Mercedes E63 AMG Wagon --> we extract e 63 amg, try extracting trim again using e 63 amg + wagon

    return_dict =  {
        'extracted_make': make,
        'extracted_model': model,
        'extracted_trim': trim
    }

    if make != None:
        make = return_dict['extracted_make'].lower()
        return_dict['extracted_make'] = make

    for key, value in return_dict.items():
        if value == None:
            return_dict[key] = " "
        else:                                       ## Check to see if the model or trim should be mapped to an alias
            if key == 'extracted_model':
                return_dict['extracted_model'] = value.lower()
                model = value.lower()
                if make in model_lookup_dict:
                    if value.lower() in model_lookup_dict[make]:
                        return_dict['extracted_model'] = model_lookup_dict[make][value.lower()]
                        model = model_lookup_dict[make][value.lower()]
            if key == 'extracted_trim':
                return_dict['extracted_trim'] = value.lower()
                trim = value.lower()
                if make in trim_lookup_dict:
                    if value.lower() in trim_lookup_dict[make]:                 
                        return_dict['extracted_trim'] = trim_lookup_dict[make][value.lower()]
                        trim = trim_lookup_dict[make][value.lower()]

    #### NEW CODE: Greedy search to see if there is a longer trim that matches the listing
    # listing = listing.lower()
    # newer_trim = None

    # if make:
    #     listing = listing.replace(make.lower(), "")
    # if model:
    #     listing = listing.replace(model.lower(), "")
    # if trim:
    #     newer_trim_to_extract = listing
    #     if make:
    #         still_searching = True
    #         if model:
    #             trims_to_search = car_data[make.lower()][model.lower()]
    #         else:
    #             trims_to_search = [trim for trim in models for model in car_data[make.lower()]]

    #         # tts = all_trims.remove(trim) 
    #         # newer_trim = get_closest_match(newer_trim_to_extract, trims_to_search) 
    #         trims_to_remove_from_search = []
    #         if make in trim_lookup_dict:
    #             trim_alias_dict = trim_lookup_dict[make]
    #             trims_to_remove_from_search = keys_for_value(trim_alias_dict, trim)          # Remove all trims which are currently equal to found trim
    #         trims_to_remove_from_search.append(trim)
    #         tts_full = remove_sublist_elements(trims_to_search, trims_to_remove_from_search)
    #         tts = [t for t in tts_full if len(t) > len(trim)]
    #         # print("Older trim: ")
    #         # print(trim)
    #         # print("Newer trim to extract: ")
    #         # print(newer_trim_to_extract)
    #         # print("TTS: ")
    #         # print(tts)

    #         while still_searching:  
    #             newer_trim_2, _= get_closest_match(newer_trim_to_extract, tts, similarity_threshold=0.85)
    #             if newer_trim_2 == None:
    #                 still_searching = False
    #             else:
    #                 newer_trim = newer_trim_2
    #                 tts.remove(newer_trim)

    # if newer_trim != None:
    #     "FOUND NEWER TRIM"
    #     return_dict['Trim'] = newer_trim
    #     if make in trim_lookup_dict:
    #         if newer_trim in trim_lookup_dict[make]:                 
    #             return_dict['Trim'] = trim_lookup_dict[make][newer_trim]


    return return_dict 


def extract_make_only(make, similarity_threshold=0.75):
    if make == None:
        return None, 0 
    
    found_make,similarity = get_closest_match(make, car_makes)

    if found_make != None and found_make.lower() == "mercedes":
        found_make = "mercedes-benz"
    
    if found_make != None and found_make.lower() == "vw":
        found_make = "volkswagen"
    
    if found_make != None and found_make.lower() == "rr":
        found_make = "rolls-royce"

    if found_make != None and found_make.lower() == "chevy":
        found_make = "chevrolet"

    return found_make, similarity

def extract_model_only(model, found_make = None, similarity_threshold=0.75):
    # doc = nlp(trim)
    found_model = None
    similarity=0 

    if found_make != " " and model != " ":
        make = found_make 

        models = car_data[make.lower()].keys()
        found_model, similarity = get_closest_match(model, models, similarity_threshold)
    
    else:      # If found_make is passed as None, search all models to see if there's a match
        # print("WIP: Need to figure out what to do when found_make is passed as None...")
        all_models = [model for model in make.keys() for make in car_data.keys()]
        found_model, similarity = get_closest_match(model, all_models, similarity_threshold)
    
    if found_model:             # Match model with lookup_dict 
        if found_make in model_lookup_dict:
            if found_model in model_lookup_dict[make]:
                found_model = model_lookup_dict[make][found_model]

    return found_model, similarity 

# input make / model if we already know what it could be
def extract_trim_only(trim, found_make = None,  found_model = None, similarity_threshold=0.75):
    # doc = nlp(trim)
    #found_trim = None
    similarity = 0 

    if found_make != " " and found_model != " " and trim:
        make = found_make 
        model = found_model

        trims = car_data[make.lower()][model.lower()]
        found_trim, similarity = get_closest_match(trim, trims, similarity_threshold)

        if found_trim == None:
            found_trim, similarity = get_closest_match(trim, trims, similarity_threshold)
    
    if found_trim:
        if found_make in trim_lookup_dict:
            if found_trim in trim_lookup_dict[make]:
                found_trim = trim_lookup_dict[make][found_trim]
    
    return found_trim, similarity 

def extract_trim_from_make(trim, found_make = None, similarity_threshold=0.75):
    # doc = nlp(trim)
    found_trim = None
    similarity = 0 
    if found_make and trim:
        make = found_make
        trims=[] 
        for trim_list in car_data[found_make.lower()].values():
            for t in trim_list:
                trims.append(t)
        #trims = [trim for models in car_data[make.lower()].keys() for trims in models.values() for trim in trims]
        found_trim, similarity = get_closest_match(trim, trims, similarity_threshold)

        if found_trim == None:
            found_trim, similarity = get_closest_match(trim, trims, similarity_threshold=0.4)
    
    if found_trim:
        if found_make in trim_lookup_dict:
            if found_trim in trim_lookup_dict[make]:
                found_trim = trim_lookup_dict[make][found_trim]
    
    return found_trim, similarity 

def runTest():
    test_listings = [
        "2020 Honda Civic Sedan LX with 15,000 miles",
        "2021 Mazda CX-5 10K Miles Grand Touring",
        "2024 BMW X3 sDrive30i",
        "Tell me about the 2002 Mercedes E55 AMG?",
        "2023 Mercedes-Benz EQB250+ with 25000 miles",
        "2024 Alfa Romeo Giulia Veloce RWD 9K Miles",
        "2016 Subaru Forester 4dr CVT 2.5i Premium PZEV",
        "Toyota Sienna LE FWD 8-Passenger (Natl) 2021 with 7.4K miles",
        "Toyota Tacoma 2WD SR5 Double Cab 6' Bed V6 AT (N",
        "2019 Jeep Cherokee Trailhawk (13,250 miles)",
        "Porsche M3 Competition Touring",
        "Type S Acura NSX Portland Oregon with under 10000 miles",
        "2000 miles 2023 Hyundai Tucson Plug-In Hybrid Limited",
        "1995 Ferrari F50",
        "2023 Ferrari F50",
        "Give me specs of the 2008 Bugatti Veyron Grand Sport",
        "2022 Volkswagen Taos S FWD",
        "2023 Mercedes-Benz E 350 4MATIC Any mileage",
        "2007 Saab 9-3 Aero",
        "2020 Rolls-Royce Cullinan Black Badge",
        "2024 Audi A5 Sportback 45 TFSI Quattro Premium Plus",
        "2016 Chevy Cruze in Newark, NJ",
        "2021 Buick Encore GX AWD Essence",
        "Tesla S Model Plaid",
        "2005 Mercedes S Class AMG",
        "2009 Saturn Astra < 30K miles",
        # "The weather in Belgrade today is 26.3 celsius. Overall, the weather in 2024 has been pretty nice. I might go outside to drive my Mercedes.",
        # "The drive from Paris to Milan is around 530 miles, which is about the same as the drive from Georgia to Miami.",
        #"et1e t4obmwtoiu1lnt acuraoghq",
        "What cars are similar to the Honda CR-V?",
        #"Is the Rimac Nevera the fastest car in the world?",
        "What are pros and cons of the 2022 F-150?",
        "2024 Corolla",
        "2021 Chrysler 300 300S RWD less than 28,000 miles",
        "2018 AMG G Wagon Miami Florida",
        "2022 Chevy Equinox ls with < 10K miles",
        "1991 ZR1 Corvette",
        "2007 Mercedes C350 Sport 6MT - 1 of 50 in US - $7,000",
        "2015 BMW 320i Standard Driven 95,000 miles",
        "2011 Aston Martin V12 Queens",
        "ML 320 Mercedes-Benz (Modeal Year: 2000)",
        "2011 Mazda3 Touring",
        "Which one should I buy? Ram 1500 TRX or Ford Raptor?",
        "2003 Mitsubishi Galant 4-Cyl",
        "How similar are the Audi RSQ8 and the Lamborghini Urus Performante?",
        "Used 2016 Porsche 911 Carrera Black Edition Coupe 2D",
        "2002 Caddilac Escalade Bellerose Long Island 150k Mile",
        "Exceptionally Clean Smart Car 453 - $9,000",
        "VOLVO XC70 70K MILES ",
        "2001 BMW 740il Black on Black low 100 K miles (Great Condition in and out). No lowball offers",
        "GLB SUV 250",
        "Mercedes E63 AMG Wagon",
        "Mercedes GLS Maybach",
        "Lexus NX 450h",
        "2022 Lexus is500 under 30,000 miles",
        "BMW m3",
        "AUDI R8 SPYDER COUPE V10",
        "Dodge Challenger Hellcat Widebody jail break",
        "dodge daytona iroc rt",
        "bmw 3-series 340i",
        "lexus is500"
    ]

    start_time = time.time()
    with open('CORRECTED_results.txt', 'w') as file:
        for listing in test_listings:
            # print(listing)
            file.write(f"\nListing: {listing}\n")
            result = extract_info(listing)
            for key, value in result.items():
                file.write(f"{key}: {value}\n")
            
    end_time = time.time()
    elapsed_time = end_time - start_time

    with open('CORRECTED_results.txt', 'a') as file:
        file.write(f"\nTotal time elapsed: {elapsed_time:.2f} seconds\n")


def main():
    test_input = "bmw x3 m50"
    #test_input = "lexus nx450h plus"
    #res = extract_trim_only("amg", "mercedes-benz", "s-class")

    # split = split_string_on_letter_number_transition(test_input)
    # print("testing splitter")
    # print(split)
    
    start_time = time.time()
    res = extract_info(test_input)
    end_time = time.time()
    total_time = end_time - start_time

    print(f"Extracting: {test_input}")
    print(f"RES: {res}")
    print(f"TOTAL TIME: {total_time}")
    # s = ['iroc r/t', 'shelby']
    # input = 'iroc rt'
    # g = get_closest_match(input, s, similarity_threshold=0.75)
    # print(g)


    #runTest()

if __name__ == "__main__":
    main()