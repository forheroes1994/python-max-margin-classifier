from instence import *
from hyperparameter import Hyperparameter
import numpy as np
import sys
import re
import os
import random
import torch
import time


torch.manual_seed(666)
random.seed(666)
np.random.seed(666)

class Classifier:
    def __init__(self):
        self.feature_alphabet = feature_alphabet()
        self.hyperparameter_1 = Hyperparameter()
        self.bias = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
        self.average_bias = np.array([0.0, 0.0, 0.0, 0.0, 0.0])


    def clean_str(self,string):
        """
        Tokenization/string cleaning for all datasets except for SST.
        Original taken from https://github.com/yoonkim/CNN_sentence/blob/master/process_data.py
        """
        string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
        string = re.sub(r"\'s", " \'s", string)
        string = re.sub(r"\'ve", " \'ve", string)
        string = re.sub(r"n\'t", " n\'t", string)
        string = re.sub(r"\'re", " \'re", string)
        string = re.sub(r"\'d", " \'d", string)
        string = re.sub(r"\'ll", " \'ll", string)
        string = re.sub(r",", " , ", string)
        string = re.sub(r"!", " ! ", string)
        string = re.sub(r"\(", " \( ", string)
        string = re.sub(r"\)", " \) ", string)
        string = re.sub(r"\?", " \? ", string)
        string = re.sub(r"\s{2,}", " ", string)
        return string.strip().lower()

    def read_file(self, path):
        Inst_list = []
        f = open(path, encoding = "UTF-8")
        for line in f.readlines():
            m_1 = inst()
            x = line.strip().split('|||')
            m_1.word = self.clean_str(x[0]).split(' ')
            m_1.label = x[1].strip()
            Inst_list.append(m_1)
        f.close()
        return Inst_list

    def extract_sentence_feature_and_label_encoding(self,Inst_list):
        all_inst_feature = []
        for i in Inst_list:
            example = Example()
            for idx in range(len(i.word)):
                example.word_index.append('unigram = ' + i.word[idx])
            for idx in range(len(i.word) - 1):
                example.word_index.append('bigram = ' + i.word[idx] + '#' + i.word[idx + 1])
            for idx in range(len(i.word) - 2):
                example.word_index.append('trigram = ' + i.word[idx] + '#' + i.word[idx + 1] + '#' + i.word[idx + 2])
            if i.label == '0':
                example.label_index = [0, 0, 0, 0, 1]
                example.max_label_index = 4
            elif i.label == '1':
                example.label_index = [0, 0, 0, 1, 0]
                example.max_label_index = 3
            elif i.label == '2':
                example.label_index = [0, 0, 1, 0, 0]
                example.max_label_index = 2
            elif i.label == '3':
                example.label_index = [0, 1, 0, 0, 0]
                example.max_label_index = 1
            elif i.label == '4':
                example.label_index = [1, 0, 0, 0, 0]
                example.max_label_index = 0

            # if i.label == '0':
            #     example.label_index = 0
            #     example.max_label_index = 1
            # elif i.label == '1':
            #     example.label_index = 0
            #     example.max_label_index = 1
            # # elif i.label == '2':
            # #     example.label_index = [0, 0, 1, 0, 0]
            # #     example.max_label_index = 2
            # elif i.label == '3':
            #     example.label_index = 1
            #     example.max_label_index = 0
            # elif i.label == '4':
            #     example.label_index = 1
            #     example.max_label_index = 0
            all_inst_feature.append(example)
        return all_inst_feature

    def creat_feature_alphabet(self, Inst_list):
        words = []
        for i in Inst_list:
            for j in i.word:
                words.append(j)
        featurealphabet = self.feature_alphabet.add_feature_alphabet(words)
        return featurealphabet

    def one_hot_encoding(self, train_Inst, dataset):
        one_hot_list = []
        all_Inst_feature = self.extract_sentence_feature_and_label_encoding(dataset)
        feat_alphabet = self.creat_feature_alphabet(train_Inst)
        for exam in all_Inst_feature:
            one_hot = Example()
            one_hot.label_index = exam.label_index
            one_hot.max_label_index = exam.max_label_index
            for j in exam.word_index:
                if j in feat_alphabet.dict:
                    one_hot.word_index.append(feat_alphabet.dict[j])
            one_hot_list.append(one_hot)
        return one_hot_list

    def Init_weight_array(self, train_Inst):
        feat_alphabet =self.creat_feature_alphabet(train_Inst)
        self.weight_array = np.random.rand(len(feat_alphabet.list), self.hyperparameter_1.class_num)
        return self.weight_array

    def get_other_max_index(self, result, true_idx):
        result_1 = result.tolist()
        del result_1[true_idx]
        other_max, other_index = result_1[0], 0
        for idx in range(len(result_1)):
            if result_1[idx] > other_max:
                other_max, other_index = result_1[idx], idx
            else:
                continue
        for idx in range(len(result)):
            if idx != true_idx:
                if result[idx] == other_max:
                    other_index = idx
        return other_max, other_index

    def get_max_index(self, result):
        max, index = result[0],0
        for idx in range(len(result)):
            if result[idx] > max:
                max, index = result[idx], idx
        return index

    def Y_list(self, one_hot_list):
        y_list = []
        for idx in one_hot_list:
            sentence_result = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
            for j in idx.word_index:
                sentence_result += np.array(self.weight_array[j])
            for i in range(len(sentence_result)):
                if i != idx.max_label_index:
                    sentence_result[i] = sentence_result[i] + self.hyperparameter_1.r
            y_list.append(sentence_result)
        return y_list

    def set_batchBlock(self, examples):
        if len(examples) % self.hyperparameter_1.batch_size == 0:
            batchBlock = len(examples) // self.hyperparameter_1.batch_size
        else:
            batchBlock = len(examples) // self.hyperparameter_1.batch_size + 1
        return batchBlock

    def start_and_end_pos(self, every_batchBlock, train_exam_list):
        start_pos = every_batchBlock * self.hyperparameter_1.batch_size
        end_pos = (every_batchBlock + 1) * self.hyperparameter_1.batch_size
        if end_pos >= len(train_exam_list):
            end_pos = len(train_exam_list)
        return start_pos, end_pos

    def softmax(self, result):
        result_list = []
        bottom = 0
        max_idx = self.get_max_index(result)
        for index, value in enumerate(result):
            bottom += np.exp(value - result[max_idx])
        for index, value in enumerate(result):
            result_list.append(np.exp(value - result[max_idx])/bottom)
        return result_list

    def judge_margin(self, result, true_idx, other_max):
        # for i in range(len(result)):
        #     if i != true_idx:
        #         if result[true_idx] <= result[other_max_idx]:
        #             return False
        #     else:
        #         continue
        # return True
        if result[true_idx] <= other_max:
            return False
        else:
            return True


    def train(self, train_Inst, dev_Inst, test_Inst):
        train_exam_list = self.one_hot_encoding(train_Inst, train_Inst)
        dev_exam_list = self.one_hot_encoding(train_Inst, dev_Inst)
        test_exam_list = self.one_hot_encoding(train_Inst, test_Inst)
        feat_alphabet = self.creat_feature_alphabet(train_Inst)
        self.weight_array = np.zeros((len(feat_alphabet.list), self.hyperparameter_1.class_num))
        train_size = len(train_exam_list)
        for epoch in range(1, self.hyperparameter_1.epochs + 1):
            print("————第{}轮迭代，共{}轮————Time = {}".format(epoch, self.hyperparameter_1.epochs, time.time()))
            corrects, accuracy, sum, steps, all_loss = 0, 0, 0, 0, 0
            random.shuffle(train_exam_list)
            batchBlock = self.set_batchBlock(train_exam_list)
            for every_batchBlock in range(batchBlock):
                start_pos, end_pos = self.start_and_end_pos(every_batchBlock, train_exam_list)
                sentence_result = self.Y_list(train_exam_list[start_pos:end_pos])
                for idx in range(len(sentence_result)):
                    steps += 1
                    sum += 1
                    other_word_max, other_word_max_idx = self.get_other_max_index(sentence_result[idx],train_exam_list[start_pos + idx].max_label_index)
                    if self.judge_margin(sentence_result[idx], train_exam_list[start_pos + idx].max_label_index, other_word_max)is not True:
                        all_loss += 1
                        for i in train_exam_list[start_pos + idx].word_index:
                            self.weight_array[i][other_word_max_idx] -= self.hyperparameter_1.r
                            self.weight_array[i][train_exam_list[start_pos + idx].max_label_index] += self.hyperparameter_1.r
                    else:
                        corrects += 1
            if steps % self.hyperparameter_1.log_interval == 0:
                accuracy = corrects / sum * 100.0
                sys.stdout.write(
                    '\rBatch[{}/{}] - loss: {:.6f}  acc: {:.4f}%({}/{})'.format(steps,
                                                                                train_size,
                                                                                all_loss,
                                                                                accuracy,
                                                                                corrects,
                                                                                sum))
            if steps % self.hyperparameter_1.test_interval == 0:
                self.eval(dev_exam_list)

    def eval(self, dev_exam_list):
        corrects, accuracy, sum = 0, 0, 0
        train_size = len(dev_exam_list)
        for idx in range(len(dev_exam_list)):
            sum += 1
            sentence_result = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
            for i in dev_exam_list[idx].word_index:
                sentence_result += np.array(self.weight_array[i])
            sentence_result += self.hyperparameter_1.r
            word_max, word_max_index = self.get_other_max_index(sentence_result, dev_exam_list[idx].max_label_index)
            if self.judge_margin(sentence_result, dev_exam_list[idx].max_label_index, word_max) is True:
            # if self.get_max_index(sentence_result) == dev_exam_list[idx].max_label_index:
                corrects += 1
        accuracy = corrects / sum * 100.0
        print('\nEvaluation -  acc: {:.4f}%({}/{}) \n'.format(accuracy,
                                                                  corrects,
                                                                  train_size))



a = Classifier()
train_Inst = a.read_file(path='data/raw.clean.train')
#train_Inst = a.read_file(path='data/raw.clean.test')
# train_Inst = a.read_file(path='data/train_data')
dev_Inst = a.read_file(path='data/raw.clean.dev')
test_Inst = a.read_file(path='data/raw.clean.test')
if os.path.exists("./Test_Result.txt"):
    os.remove("./Test_Result.txt")
    print("The 'Test_Result.txt' has been removed.")
    a.train(train_Inst, dev_Inst, test_Inst)
else:
    a.train(train_Inst, dev_Inst, test_Inst)