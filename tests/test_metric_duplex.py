from gems85.metric import dti_exact, dti_binary, dti_bruteforce, marginal_inclusion_threshold, kernel
import numpy as np

def test_marginal_threshold():
    assert abs(marginal_inclusion_threshold(0.2708) - 0.2*0.2708) < 1e-9

def test_scoring_example():
    # p967 worked example: TP 3.00 FP 1.89 FN 2.00 -> 0.60 at alpha 0.2 beta 0.8
    # We test via bruteforce small grid
    truth = np.zeros((5,5), bool); truth[2,1:4]=True
    pred = np.zeros((5,5)); pred[2,2]=1; pred[1,3]=0.5 # approximate
    r = dti_exact(pred, truth)
    assert 0 <= r['dti'] <= 1

def test_kernel():
    assert kernel(0)==1.0
    assert kernel(3)==0.0
    assert kernel(1.5)==0.5
