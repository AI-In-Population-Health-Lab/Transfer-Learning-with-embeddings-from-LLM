from model_method import processDataset, llm_embedding, llm_embedding_2, emb_dic, splitTrainValTest, model_running, performance, changeOrder
from cnn_feedforward import CNN_feedforward
import torch

disease="FLU"
batch_size=32
epoch=50
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

disease_label="delete M"  #"delete M"      #"M to F"
cui_label= "M to A"    #"M to A"
source='AC'
target='SLC'

baselines=[True,False]
llms=['bert','biobert','medbert','openai_small','openai_large']
for baseline in baselines:
    for llm in llms:
        if baseline:
            llm='onehot'

        df= processDataset(f"data/cleaned_{target}.xlsx", disease, disease_label, cui_label, False,False)
        # df=changeOrder(df)
        print(df.shape)

        if baseline:
            cui2idx, embedding_matrix=emb_dic(df, baseline)
        # embedding_cui= llm_embedding_2("/Users/yuhe/Desktop/AIPH/weekly/2023/2023.12/embeddings_project8/UMLS_code_openai.h5", "/Users/yuhe/Desktop/AIPH/weekly/2023/2023.12/embeddings_project8/UMLS_code2_openai.h5")
        else:
            llm_emb=f"cui_embeddings/concept_pair_{llm}.h5"
            embedding_cui=llm_embedding(llm_emb)
            cui2idx, embedding_matrix=emb_dic(df, baseline, embedding_cui)

        print(embedding_matrix)


        train_loader, val_loader, test_loader, cui_channel=splitTrainValTest(df, disease, batch_size, cui2idx)
        print(cui_channel)

        # seeds=[215]
        # seeds=[401]
        seeds=[215, 401, 114514]
        seeds_n=''
        for i in seeds:
            seeds_n+="_"+str(i)

        stride=1
        padding=0

        if baseline:
            inchannels=embedding_matrix.shape[0]
        else:
            inchannels=len(embedding_cui.columns)

        print(f"LLM {llm}")
        print("Starting training model: ")

        classifier = CNN_feedforward(pretrained_embedding=embedding_matrix, cuis_size=len(cui2idx), in_channels=inchannels, stride=stride, padding=padding, filter_sizes=[1])
        classifier.load_state_dict(torch.load(f'model_path/0913/{source}_best_model_{llm}.pth'))
        classifier.to(device)
        # classifier,log=model_running(device, train_loader, val_loader,embedding_matrix, cui2idx, seeds, epoch, in_channels=inchannels, stride=stride, padding=padding,filter_sizes=[2,3,4],llm=llm,source=source)
        # classifier=model_running(device, train_loader, val_loader,embedding_matrix, cui2idx, seed, epoch, in_channels=len(embedding_cui.columns), stride=stride, padding=padding, filter_sizes=[cui_channel])  ## only 1 filter with width of all channel
        # classifier=model_running(device, train_loader, embedding_matrix, cui2idx, seed, epoch, in_channels=cui_channel, stride=stride, padding=padding)

        result_name=f"best_results/{source}2{target}_noTune_best_result_{llm}_bs{batch_size}_e{epoch}_seed{seeds_n}"

        print("############## Model Setting ###############")
        print('llm: ', llm)
        print("Batch Size: ", batch_size)
        print("Epoch: ", epoch)
        print("Seed: ", seeds)
        print("Stride: ", stride)
        print("Padding: ", padding)
        print("Disease_label:", disease_label)
        print("CUI_label: ",cui_label)

        print("############## Model performance #############")
        print("test performance:")
        r1=performance(device, classifier, test_loader,result_name+"_test.csv")
        # print("train performance:")
        # r2=performance(device, classifier, train_loader,result_name+"_train.csv")

        log_name=f"experimentLog/{source}2{target}_noTune_experiment_log_{llm}_bs{batch_size}_e{epoch}_seed{seeds_n}.txt"

        with open(log_name,'w') as f:
            f.write("##############  AC Model Setting ###############\n")
            f.write('llm: %s \n' % llm)

            f.write("Batch Size: %s \n" % batch_size)
            f.write("Epoch: %s \n" % epoch)
            f.write("Seed: %s \n" % seeds)
            f.write("Stride: %s \n" % stride)
            f.write("Padding: %s \n" % padding)
            f.write("Disease_label: %s \n" % disease_label)
            f.write("CUI_label: %s \n" % cui_label)

            # f.write("\n############## Start Training Model ###############\n")
            # f.write(log)
            # f.write("Training Complete.\n")

            f.write("\n############## Model performance #############\n")
            f.write("test performance: \n")
            f.write(r1)
            # f.write("train performance: \n")
            # f.write(r2)
        f.close()
        print(f"{llm} End")
        if baseline:
            break