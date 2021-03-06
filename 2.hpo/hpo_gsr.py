"""
@Author: Bart-Jan Boverhof
@Last Modified by: Bart-Jan Boverhof
@Description This file conducts the hyper-paramater optimization for sigle-modular GSR networks on GPU.
BEWARE! Running this code on a machine with NVIDIA GPU is highly recommended. 
"""

import numpy as np
import torch
import os
import torch 
from torch import optim #PyTorch additionals and training optimizer
import torch.nn as nn
import torch.nn.functional as F #PyTorch library providing a lot of pre-specified functions
import os
from torch.utils.data import Dataset, DataLoader, SubsetRandomSampler
from torch import optim
from torch.nn.utils.rnn import pad_sequence
import numpy as np
import optuna 
import pickle5 as pickle

#############################################################################################
##################################### Data preperation ######################################
#############################################################################################
class PytorchDataset(Dataset):
    
    def __init__(self, path, modality):
        """
        Purpose: 
            Load pickle object and save only specified data. 
        """
        dat = pickle.load(open("...SPECIFY THE LOCATION OF THE DATA HERE..."+participant+".pickle", "rb")) #Open pickle
        key = "labels_"+modality #Determining right dict key
        self.labels = dat[key] #Saving labels
        self.dat = dat[modality] #Saving only modality of interest
        self.modality = modality

        #Determining the longest window for later use
        lengths = []
        for i in self.dat:
            lengths.append(len(i))
        longest_window = max(lengths)


    def __len__(self):
        """
        Purpose: 
            Obtain the length of the data
        """
        return len(self.dat)


    def __getitem__(self, idx):
        """
        Purpose:
            Iterater to select windows
        """
        windows = self.dat[idx]
        labels = self.labels[idx]

        return windows, labels
    

    def __PaddingLength__(self):
        """
        Purpose:
            Determine padding length
        """
        lengths = []
        for i in self.dat:
            lengths.append(i.shape[0])
        
        return max(lengths)

    def __ObtainModality__(self):
        """
        Purpose:
            Print modality
        """
        
        return self.modality


#Batch transformation class
class BatchTransformation():
    def __call__(self, batch):
        """
        Purpose:   
            Transformation of windows per batch (padding & normalizing labels & transposing)
        """

        padding_length = self.padding_length
        modality = self.modality

        #PADDING
        sequences = [x[0] for x in batch] #Get ordered windows
        sequences.append(torch.ones(padding_length,1)) #Temporary add window of desired padding length
        sequences_padded = torch.nn.utils.rnn.pad_sequence(sequences, batch_first=True, padding_value = 0) #Pad
        sequences_padded = sequences_padded[0:len(batch)] #Remove the added window

        #Obtaining Sorted labels and standardizing
        labels = torch.tensor([x[1] for x in batch]) #Get ordered windows
        labels = (labels - 1)/ 20
        
        #TRANSPOSE BATCH 
        sequences_padded = torch.transpose(sequences_padded, 1, 2)

        return sequences_padded, labels
    
    def transfer(self):
        """
        Purpose:
            Transfering the earlier obtained padding length to the BatchTransformation class such it can be used
            in the __call__ function.
        """
        BatchTransformation.padding_length = self[0]
        BatchTransformation.modality = self[1]

#############################################################################################
######################################### Network ###########################################
#############################################################################################
class GSRNet(nn.Module):
    def __init__(self, tensor_length, out_features, drop):
        super(GSRNet, self).__init__()

        self.drop = drop
        self.tensor_length = tensor_length
        foo = int(tensor_length /3)
        foo = int(foo /3)         
        foo = int(foo /3)
        foo = int(foo /3)
        dense_input = 128*foo

        #Convolutional layers
        self.conv1 = nn.Conv1d(in_channels = 1, out_channels = 16, kernel_size = 3, padding=1)
        self.conv2 = nn.Conv1d(in_channels = 16, out_channels = 32, kernel_size = 3, padding=1)
        self.conv3 = nn.Conv1d(in_channels = 32, out_channels = 64, kernel_size = 3, padding=1)
        self.conv4 = nn.Conv1d(in_channels = 64, out_channels = 128, kernel_size = 3, padding=1)

        #Max pooling layer (3x1)
        self.pool = nn.MaxPool1d(kernel_size = 3, stride = 3) 

        #Batch normalization
        self.batch1 = nn.BatchNorm1d(num_features = 16)
        self.batch2 = nn.BatchNorm1d(num_features = 32)
        self.batch3 = nn.BatchNorm1d(num_features = 64)
        self.batch4 = nn.BatchNorm1d(num_features = 128)

        #Dense layer
        self.dense1 = nn.Linear(dense_input, out_features) 
        self.dense2 = nn.Linear(out_features, 1) 

        #Dropout layer
        self.dropout = nn.Dropout(drop)

        
    def forward(self, x): 
        x = self.pool(F.elu(self.batch1(self.conv1(x)))) #First block
        x = self.pool(F.elu(self.batch2(self.conv2(x)))) #Second block
        x = self.pool(F.elu(self.batch3(self.conv3(x)))) #Third block
        x = self.pool(F.elu(self.batch4(self.conv4(x)))) #Fourth block
        
        x = x.view(-1, x.shape[1]* x.shape[2]) #Flatten
        x = self.dropout(x)
        x = F.relu(self.dense1(x))
        x = self.dense2(x)

        return x

###########################################################################################
######################################### HPO search ######################################
###########################################################################################
def objective(trial):
    
    ###########################################################################################
    ########################## 1. Create PyTorch dataset & Loader(s) ##########################
    ###########################################################################################
    #Create PyTorch dataset definition class
    #path = "pipeline/prepared_data/"+participant+"/data.pickle"
    pydata =  PytorchDataset(path = "path", modality = modality)

    padding_length = PytorchDataset.__PaddingLength__(pydata) #Determining the longest window for later use
    BatchTransformation.transfer([padding_length, modality]) #Transfer max padding length & modality vars to BatchTransfor class
               
               
      #Making splits
    batch_size = 10
    test_split = .1
    validation_split = .1

    ################
    ## TEST SPLIT ##
    ################    
    indices_traintest = list(range(len(pydata.dat))) #Create list of indices
    test_indices = indices_traintest[::int(test_split*100)]  
    train_val_indices = [x for x in indices_traintest if x not in test_indices]

    val_indices = train_val_indices[::int(validation_split*100)]
    train_indices = [x for x in train_val_indices if x not in val_indices]
   
  
    traindata = [pydata[i] for i in train_indices]
    valdata = [pydata[i] for i in val_indices]
    testdata = [pydata[i] for i in test_indices]

    #Defining loaders
    testloader = torch.utils.data.DataLoader(testdata, #Test loader 
                                        batch_size = batch_size, 
                                        shuffle = True,
                                        drop_last= False,
                                        collate_fn = BatchTransformation())

    validloader = torch.utils.data.DataLoader(valdata, #Validation loader
                                            batch_size = batch_size, 
                                            shuffle = True,
                                            drop_last= False,
                                            collate_fn = BatchTransformation())

    trainloader = torch.utils.data.DataLoader(traindata, #Training loader
                                            batch_size = batch_size, 
                                            shuffle = True,
                                            drop_last= False,
                                            collate_fn = BatchTransformation())



    ###########################################################################################
    ################################## 2. Defining model ######################################
    ###########################################################################################
    #Determine max out_features
    max_out = int(padding_length /3)
    max_out = int(max_out /3)         
    max_out = int(max_out /3)
    max_out = int(max_out /3)
    max_out = 200*max_out
    
    out_features = trial.suggest_int("n_units", 10, max_out)
    drop = trial.suggest_float('dropout_rate', 0.2, 0.5)

    model = GSRNet(tensor_length = padding_length, drop = drop, out_features = out_features)
    
    #Hyperparams
    #Optimizer and learning rate
    lr = trial.suggest_float("lr", 1e-5, 1e-1, log = True)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()   
   
    if train_on_gpu:
        model.cuda()

    ###########################################################################################
    ########################## 3. Training & Validation loop ##################################
    ###########################################################################################

    #Prerequisites
    clip = 5
    valid_loss_min = np.Inf


    for epoch in range(1, epochs+1):
            
        valid_loss = 0.0

        ###################
        ###Training loop###
        ###################
        model.train()
        for windows, labels in trainloader:

            # move tensors to GPU if CUDA is available
            if train_on_gpu:
                windows, labels = windows.cuda(), labels.cuda()

            #Training pass
            optimizer.zero_grad()
            out = model(windows)
            loss = criterion(out.squeeze(), labels)
            loss.backward()
            optimizer.step()
        
        #VALIDATION
        model.eval()
        for windows, labels in validloader:

            # move tensors to GPU if CUDA is available
            if train_on_gpu:
                windows, labels = windows.cuda(), labels.cuda()
            
            #Test pass    
            out = model(windows)
            loss = criterion(out.squeeze(), labels)
            valid_loss += loss.item()*windows.size(0)

        #Averages losses
        valid_loss = valid_loss/len(valdata)
          
        #Save model if validation loss has decreased
        if valid_loss <= valid_loss_min:

            torch.save(model.state_dict(), "model.pt")
            valid_loss_min = valid_loss

    ###################
    ##Test loop##
    ###################
    with torch.no_grad():
      
      model.load_state_dict(torch.load("model.pt"))
      diff = torch.cuda.FloatTensor()
      
      predictions = torch.cuda.FloatTensor()
      labelss = torch.cuda.FloatTensor()

      model.eval()
      for windows, labels in testloader:

        if train_on_gpu:
            windows, labels = windows.cuda(), labels.cuda()

        #Test pass    
        out = model(windows)
        loss = criterion(out.squeeze(), labels)

        foo = (out.squeeze() - labels)
        diff = torch.cat([diff,foo])

      average_miss = sum(abs(diff))/len(testdata)

      accuracy = average_miss
      
      trial.report(accuracy, epoch)

      # Handle pruning based on the intermediate value.
      if trial.should_prune():
          raise optuna.exceptions.TrialPruned()

    return accuracy

###########################################################################################
############################################ Run ##########################################
###########################################################################################
participants = ["bci10", "bci12", "bci13", "bci17", "bci21", "bci22",
                "bci23", "bci24", "bci26", "bci27", "bci28", "bci29", "bci30", 
                "bci31", "bci32", "bci33", "bci34", "bci35", "bci36", "bci37", 
                "bci38", "bci39", "bci40", "bci41", "bci42", "bci43", "bci44"]

ntrials = 120
epochs = 80
batch_size = 10
np.random.seed(3791)
torch.manual_seed(3791)
torch.cuda.manual_seed(3791)

modality = "GSR"
train_on_gpu = torch.cuda.is_available()



if __name__ == "__main__":
    for participant in participants:
        print(participant)
        torch.cuda.empty_cache()

        study = optuna.create_study(direction="minimize", 
                                    storage="sqlite:///example.db")
        study.optimize(objective, n_trials=ntrials)

        pruned_trials = [t for t in study.trials if t.state == optuna.structs.TrialState.PRUNED]
        complete_trials = [t for t in study.trials if t.state == optuna.structs.TrialState.COMPLETE]

        print("Study statistics: ")
        print("  Number of finished trials: ", len(study.trials))
        print("  Number of pruned trials: ", len(pruned_trials))
        print("  Number of complete trials: ", len(complete_trials))

        print("Best trial:")
        trial = study.best_trial

        print("  Value: ", trial.value)

        print("  Params: ")
        for key, value in trial.params.items():
            print("    {}: {}".format(key, value))

        with open("...SPECIFY YOUR HPO SAVE LOCATION HERE..."+modality+"_"+participant+".pickle", 'wb') as handle: #Save as pickle
            pickle.dump(study.best_trial, handle, protocol=pickle.HIGHEST_PROTOCOL)

