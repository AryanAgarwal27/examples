import numpy as np 
import os 

def create_folds(
    sentences: list, 
    k: int = 10, 
    path: str = 'folds/', 
    seed: int = 0
) -> list: 
    """ 
    Creates `k` folds from `sentences` 
    
    Parameters 
    ---------- 
    sentences: list 
        sentences of the original document(s) in a nested list format, such that `sentences[i]` is 
        a list of strings that makes up that i'th sentence. The string is the same corresponding line 
        in the original document(s). 
        
    k: int, default=10 
        number of folds 
        
    path: string, default='folds/' 
        path where the folds are created. For example, by default the first fold is created at 
        'folds/fold0`, and its corresponding train/test pair is located at 'folds/fold0/train.txt' and 
        'folds/fold0/test.txt'. If `path` already exists, the operation is skipped. 
        
    seed: int, default=0 
        random seed for `np.random.seed(seed)` for reproducibility. 
        
    Returns 
    --------- 
    indices: list 
        indices in nested list format to represent the partition, such that `indices[i]` is a list of 
        indices that are included in the testing dataset for the i'th fold, and training dataset for 
        other folds. 
        
    """ 
    np.random.seed(seed) 
    indices = [i for i in range(len(sentences))] 
    np.random.shuffle(indices) 
    partitions = [[sentences[index] for index in indices[i::k]] for i in range(k)] 
    
    if os.path.exists(path): 
        print("'%s' already exists, skipping..." % path) 
    else: 
        os.system('mkdir folds') 
        for i in range(k): 
            os.system('mkdir folds/fold%d' % i) 

        def write_sentences_to_file(sentences, path): 
            for sentence in sentences: 
                for line in sentence: 
                    path.write(line) 
                path.write('\n')     

        for i in range(k): 
            train = open('folds/fold%d/train.txt' % i, "a") 
            test = open('folds/fold%d/test.txt' % i, "a") 
            for j in range(k): 
                write_sentences_to_file(partitions[j], test if i == j else train) 
            train.close() 
            test.close() 
        
    indices = [[index for index in indices[i::k]] for i in range(k)] 
    return indices 


def modified(given_words: list, sentence_tokens: list) -> bool: 
    """ 
    Checks whether given words have been modified by the tokenizer. 
    
    Parameters 
    ---------- 
    given_words: list 
        given words in nested list format, such that `given_words[i]` is a list of given words for the 
        i'th sentence in the original dataset 
        
    sentence_tokens: list 
        tokens generated by the tokenizers in nested list format, such that `sentence_tokens[i]` is a 
        list of tokens for the i'th sentence processed by the tokenizer 
        
    Returns 
    --------- 
    is_modified: bool 
        whether the given words have been modified 
    """ 
    for word, token in zip(given_words, sentence_tokens): 
        if ''.join(word) != ''.join(token): 
            return True  
    return False 


def get_pred_probs(scores: np.ndarray, tokens: list, given_token: list, weighted: bool = False) -> np.ndarray: 
    """ 
    Obtain `pred_probs` for one particular sentence. Maps and reduces subword-level tokens to the given 
    word-level tokens in the original dataset. 
    
    Parameters 
    ---------- 
    scores: np.array 
        np.array with shape `(N', K)`, where N' is the number of tokens of the sentence generated by the 
        tokenizer, and K is the number of classes of the model prediction. `scores[i][j]` indicates the 
        model-predicted probability that the i'th token belongs to class j. 
    
    tokens: list 
        list of tokens with length N' generated by the tokenizer. 
    
    given_token: list 
        list of given tokens with length N, where N is the number of tokens of the sentence from the 
        original dataset. 
    
    weighted: bool, default=False 
        whether to merge the probabilities using a weighted average (or unweighted average). The weight 
        is proportional to the length of the subword-level token. 
        
    Returns 
    --------- 
    pred_probs: np.array 
        np.array with shape `(N, K)`, where `pred_probs[i][j]` is the model-predicted probability that the 
        i'th token belongs to class j after processing (reducing subwords to words, and spliting words 
        merged by the tokenizers). 
        
    """ 
    i, j = 0, 0 
    pred_probs = [] 
    for token in given_token: 
        i_new, j_new = i, j 
        acc = 0 
        
        weights = []         
        while acc != len(token): 
            token_len = len(tokens[i_new][j_new:]) 
            remain = len(token) - acc 
            weights.append(min(remain, token_len)) 
            if token_len > remain: 
                acc += remain 
                j_new += remain 
            else: 
                acc += token_len 
                i_new += 1 
                j_new = 0 
        
        if i != i_new: 
            probs = np.average(scores[i:i_new], axis=0, weights=weights if weighted else None) 
        else: 
            probs = scores[i] 
        i, j = i_new, j_new 
        
        pred_probs.append(probs) 
        
    return np.array(pred_probs) 


def to_dict(nl: list) -> dict: 
    """ 
    Convert nested list to a dictionary for storing `.npz` 
    
    Parameter 
    ---------- 
    nl: list 
        information in nested list structure 
        
    Returns 
    --------- 
    d: dictionary 
        dictionary with keys as index (converted to string) of the nested list, such that `d[str(i)] == nl[i]`. 
    """ 
    return {str(i): l for i, l in enumerate(nl)} 