# used in baseline models
from typing import Optional, List, Dict
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from dalib.modules.classifier import Classifier as ClassifierBase

# def data_embedding_align(source_train, target_train, target_test, embedding_df):
#     emb_list=list(embedding_df['Unnamed: 0'])
#     cui=target_test.columns.to_list()
#     cui2=[]
#     for i in cui:
#         if i in emb_list:
#             cui2.append(i)
#     target_test=target_test.loc[:,cui2]
#     target_train=target_train.loc[:,cui2]
#     source_train=source_train.loc[:,cui2]
#     embedding_df=embedding_df[embedding_df['Unnamed: 0'].isin(cui2)]
#     return source_train, target_train, target_test, embedding_df



# def patient_cui(df):
#     patients_cui={}
#     col=df.columns
#     for row in df.itertuples():
#         patients_cui[row[0]]=[]
#         for i,j in enumerate(col):
#             patients_cui[row[0]].append(j+'_'+row[1:][i])
#     return patients_cui



class CNN_feedforward(nn.Module):
    def __init__(self, pretrained_embedding=None,
                 freeze_embedding=True,
                 cuis_size=None,
                 embed_dim=768,
                 filter_sizes=[2,3,4],
                 num_filters=[100,100,100],
                 num_classes=2,
                 dropout=0.5):
        super(CNN_feedforward, self).__init__()
        # Embedding layer
        if pretrained_embedding is not None:
            self.cuis_size, self.embed_dim = pretrained_embedding.shape
            self.embedding = nn.Embedding.from_pretrained(pretrained_embedding,
                                                          freeze=freeze_embedding)
        else:
            self.embed_dim = embed_dim
            self.embedding = nn.Embedding(num_embeddings=cuis_size,
                                          embedding_dim=self.embed_dim,
                                          padding_idx=0,
                                          max_norm=5.0)


        # number_of_channel = symptom_size
        kernel_size = 3  # Size of the convolutional kernel
        stride = 1  # Stride for the convolution
        padding = 1  # Padding for the input
       
       # Conv Network
        self.conv1d_list = nn.ModuleList([
            nn.Conv1d(in_channels=1,   #in_channels=self.embed_dim,
                      out_channels=num_filters[i],
                      kernel_size=filter_sizes[i])
            for i in range(len(filter_sizes))
        ])
        # Fully-connected layer and Dropout
        self.fc = nn.Linear(np.sum(num_filters), num_classes)
        self.dropout = nn.Dropout(p=dropout)
        # # self.conv1 = nn.Conv2d(number_of_channel, number_of_classes, kernel_size, stride, padding)
        # self.conv1 = nn.ModuleList([
        #     nn.Conv2d(1, number_of_channel, (fs, embedding_dim)) for fs in filter_sizes
        # ])
        self.pool = nn.MaxPool2d(kernel_size, stride, padding)


    def forward(self, input_ids):
        # print("x dtype")
        # print(x.dtype)
        # x = x.long()
        # print(x.dtype)
        # print(x.size())
        # x = self.embedding(x)
        # x = self.pool(F.relu(self.conv1(x)))
        # x = self.pool(F.relu(self.conv2(x)))
        # # x = torch.flatten(x, 1)  # flatten all dimensions except batch
        # x = self.fc3(x)

        """Perform a forward pass through the network.

        Args:
            input_ids (torch.Tensor): A tensor of token ids with shape
                (batch_size, max_sent_length)

        Returns:
            logits (torch.Tensor): Output logits with shape (batch_size,
                n_classes)
        """

        # Get embeddings from `input_ids`. Output shape: (b, max_len, embed_dim)
        x_embed = self.embedding(input_ids.long()).float()
        

        # Permute `x_embed` to match input shape requirement of `nn.Conv1d`.
        # Output shape: (b, embed_dim, max_len)
        x_reshaped = x_embed.permute(0, 2, 1)

        # Apply CNN and ReLU. Output shape: (b, num_filters[i], L_out)
        x_conv_list = [F.relu(conv1d(x_reshaped)) for conv1d in self.conv1d_list]

        # Max pooling. Output shape: (b, num_filters[i], 1)
        x_pool_list = [F.max_pool1d(x_conv, kernel_size=x_conv.shape[2])
            for x_conv in x_conv_list]
        
        # Concatenate x_pool_list to feed the fully connected layer.
        # Output shape: (b, sum(num_filters))
        x_fc = torch.cat([x_pool.squeeze(dim=2) for x_pool in x_pool_list],
                         dim=1)
        
        # Compute logits. Output shape: (b, n_classes)
        logits = self.fc(self.dropout(x_fc))

        return logits
