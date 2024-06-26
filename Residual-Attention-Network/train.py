from __future__ import print_function, division
import torch
import torch.nn as nn
import torch.optim as optim
from torch.autograd import Variable
from torch.utils.data import Dataset, DataLoader, random_split
import numpy as np
import torchvision
from torchvision import transforms, models, datasets
import os
# import cv2
import time
from model.SteelDataset import SteelDataset
# from model.residual_attention_network_pre import ResidualAttentionModel

from model.residual_attention_network import ResidualAttentionModel_92_32input_update as ResidualAttentionModel

model_file = 'model_92_sgd.pkl'


# for test
def test(model, test_loader, btrain=False, model_file='model_92.pkl'):
    # Test
    if not btrain:
        model.load_state_dict(torch.load(model_file))
    model.eval()

    correct = 0
    total = 0
    #
    class_correct = list(0. for i in range(7))
    class_total = list(0. for i in range(7))

    for images, labels in test_loader:
        # images = Variable(images.cuda())
        # labels = Variable(labels.cuda())
        images = Variable(images)
        labels = Variable(labels)
        outputs = model(images)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels.data).sum()
        #
        c = (predicted == labels.data).squeeze()
        for i in range(labels.size(0)):
            label = labels.data[i]
            class_correct[label] += c[i]
            class_total[label] += 1

    print('Accuracy of the model on the test images: %d %%' % (100 * float(correct) / total))
    print('Accuracy of the model on the test images:', float(correct)/total)
    for i in range(7):
        if class_total[i] != 0:
            print('Accuracy of %5s : %2d %%' % (
                classes[i], 100 * class_correct[i] / class_total[i]))
        else:
            print('No instances of %5s in the test set.\n' % (classes[i]))
    return correct / total


if __name__ == '__main__':

    # Image Preprocessing
    data_transforms2 = transforms.Compose([
                transforms.Resize(size=(150,2300)),
                transforms.Grayscale(3),
                transforms.ToTensor(),
                transforms.Normalize([0.5, 0.7, 0.5], [0.222, 0.226, 0.333]) ])   
    

    # Image Preprocessing
    transform = transforms.Compose([
        transforms.RandomHorizontalFlip(),
        transforms.RandomCrop((32, 32), padding=4),   #left, top, right, bottom
        # transforms.Scale(224),
        transforms.ToTensor()
    ])

    test_transform = transforms.Compose([
        transforms.ToTensor()
    ])
    # when image is rgb, totensor do the division 255

    # Define paths to your image directories
    root_dir = "C:/Users/DELL/OneDrive/Documents/isend/ResidualAttentionNetwork-pytorch/IMAGES/DEFECTS" #"./IMAGES"
    dataset = SteelDataset(root_dir, transform=data_transforms2)
    # print(dataset.__len__())

    train_size = int(0.8 * len(dataset))
    test_size = len(dataset) - train_size
    train_dataset, test_dataset = random_split(dataset, [train_size, test_size])
    train_loader = DataLoader(dataset=train_dataset,
                                            batch_size=2, 
                                            shuffle=True,
                                              num_workers=8)
    test_loader = DataLoader(dataset=test_dataset,
                                            batch_size=2,
                                            shuffle=False)

    
    classes = ('broken', 'cracks', 'dents', 'depressions', 'hairs', 'incrustations', 'irregular overlaps')
    n_classes = len(classes)
    # model = ResidualAttentionModel().cuda()
    model = ResidualAttentionModel(n_classes)
    # print(model)

    lr = 0.1  # 0.1
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=lr, momentum=0.9, nesterov=True, weight_decay=0.0001)
    is_train = True
    is_pretrain = False
    acc_best = 0
    total_epoch = 30
    if is_train is True:
        if is_pretrain == True:
            model.load_state_dict((torch.load(model_file)))

        # Training
        for epoch in range(total_epoch):
            model.train()
            tims = time.time()
            for i, (images, labels) in enumerate(train_loader):
                # images = Variable(images.cuda())
                # images = Variable(images)
                # print(images.data)
                # labels = Variable(labels.cuda())
                # labels = Variable(labels)

                # Forward + Backward + Optimize
                optimizer.zero_grad()
                outputs = model(images)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                if (i+1) % 20 == 0:
                    print("Epoch [%d/%d], Iter [%d/%d] Loss: %.4f" %(epoch+1, total_epoch, i+1, len(train_loader), loss.item()))
            print('the epoch takes time:',time.time()-tims)
            print('evaluate test set:')
            acc = test(model, test_loader, btrain=True)
            if acc > acc_best:
                acc_best = acc
                print('current best acc,', acc_best)
                torch.save(model.state_dict(), model_file)

            # Decaying Learning Rate
            if (epoch+1) / float(total_epoch) == 0.3 or (epoch+1) / float(total_epoch) == 0.6 or (epoch+1) / float(total_epoch) == 0.9:
                lr /= 10
                print('reset learning rate to:', lr)
                for param_group in optimizer.param_groups:
                    param_group['lr'] = lr
                    print(param_group['lr'])
                # optimizer = torch.optim.Adam(model.parameters(), lr=lr)
                # optim.SGD(model.parameters(), lr=lr, momentum=0.9, nesterov=True, weight_decay=0.0001)
        # Save the Model
        torch.save(model.state_dict(), 'last_model_92_sgd.pkl')

    else:
        test(model, test_loader, btrain=False)
