"""
@Author: Bart-Jan Boverhof
@Last Modified by: Bart-Jan Boverhof
@Description: This file contains the code from which all already trained networks networks are tested.
"""

#############################################################################################
######################################### Prerequisites #####################################
#############################################################################################
#Importing packages
import numpy as np
import torch
import os
import pickle

#Import local files
try:
    import loop_single, loop_multi, utility
except ModuleNotFoundError:
    wd = os.getcwd()
    print("Error: please make sure that working directory is set as '~/Masterthesis'.")
    print("Current working directory is:", wd)


#Included participants
participants = ["bci10", "bci12", "bci13", "bci17", "bci21", "bci22",
                "bci23", "bci24", "bci26", "bci27", "bci28", "bci29", "bci30", 
                "bci31", "bci32", "bci33", "bci34", "bci35", "bci36", "bci37", 
                "bci38", "bci39", "bci40", "bci41", "bci42", "bci43", "bci44"]




modalities = ["EEG"]


#############################################################################################
################################ Train Single-modality networks #############################
#############################################################################################
np.random.seed(3791)
torch.manual_seed(3791)
torch.cuda.manual_seed(3791)

epochs = 250
batch_size = 10


for modality in modalities:

    #Select correct hpo file
    hpo = pickle.load(open("hpo/hyper_parameters/"+modality+".pickle", "rb"))   
    
    for i in participants:

        loop_single.SingleTrainLoop(participant = i, modality = modality,
                        batch_size = batch_size, hpo = hpo,
                        epochs = epochs, trainortest = "train")


#############################################################################################
#############################################################################################
################################### Multi-modality networks #################################
#############################################################################################
#############################################################################################

for i in participants:
    
    #Select correct hpo file
    hpo = pickle.load(open("hpo/hyper_parameters/multi.pickle", "rb"))   
    
    #Loop
    loop_multi.MultiTrainLoop(participant = i,
                    batch_size = batch_size, hpo = hpo,
                    epochs = epochs, trainortest = "train")







