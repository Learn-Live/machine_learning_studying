# -*- coding: utf-8 -*-
r"""

"""

import copy
from collections import OrderedDict

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.utils.data as Data
from matplotlib.animation import FuncAnimation
from torch import nn, optim
from torch.utils.data import Dataset


# # matplotlib.use("Agg")
# import matplotlib.animation as manimation

def normalize_data(X, range_value=[-1, 1], eps=1e-5):  # down=-1, up=1

    new_X = np.copy(X)

    mins = new_X.min(axis=0)  # column
    maxs = new_X.max(axis=0)

    rng = maxs - mins
    for i in range(rng.shape[0]):
        if rng[i] == 0.0:
            rng[i] += eps

    new_X = (new_X - mins) / rng * (range_value[1] - range_value[0]) + range_value[0]

    return new_X


class TrafficDataset(Dataset):

    def __init__(self, X, y, transform=None, normalization_flg=False):
        self.X = X
        self.y = y
        cnt = 0
        # with open(input_file, 'r') as fid_in:
        #     line = fid_in.readline()
        #     while line:
        #         line_arr = line.split(',')
        #         value = list(map(lambda x: float(x), line_arr[:-1]))
        #         self.X.append(value)
        #         self.y.append(float(line_arr[-1].strip()))
        #         line = fid_in.readline()
        #         cnt += 1
        if normalization_flg:
            self.X = normalize_data(np.asarray(self.X, dtype=float), range_value=[-1, 1], eps=1e-5)
            # with open(input_file + '_normalized.csv', 'w') as fid_out:
            #     for i in range(self.X.shape[0]):
            #         # print('i', i.data.tolist())
            #         tmp = [str(j) for j in self.X[i]]
            #         fid_out.write(','.join(tmp) + ',' + str(int(self.y[i])) + '\n')

        self.transform = transform

    def __getitem__(self, index):

        value_x = self.X[index]
        value_y = self.y[index]
        if self.transform:
            value_x = self.transform(value_x)

        value_x = torch.from_numpy(np.asarray(value_x)).double()
        value_y = torch.from_numpy(np.asarray(value_y)).double()

        # X_train, X_test, y_train, y_test = train_test_split(value_x, value_y, train_size=0.7, shuffle=True)
        return value_x, value_y  # Dataset.__getitem__() should return a single sample and label, not the whole dataset.
        # return value_x.view([-1,1,-1,1]), value_y

    def __len__(self):
        return len(self.X)


def print_network(describe_str, net):
    num_params = 0
    for param in net.parameters():
        num_params += param.numel()
    print(describe_str, net)
    print('Total number of parameters: %d' % num_params)


def generated_train_set(num):
    X = []
    y = []
    for i in range(num):
        yi = 0
        if i % 2 == 0:
            yi = 1
        rnd = np.random.random()
        rnd2 = np.random.random()
        X.append([1000 * rnd, i * 1 * rnd2])
        y.append(yi)

    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=int)

    return TrafficDataset(X, y, normalization_flg=False)


class NerualNetworkDome():
    r"""
        test
    """

    def __init__(self):
        self.display_flg = True

        self.in_dim = 2
        self.h_dim = 1
        self.out_dim = 1

        # network structure
        in_lay = nn.Linear(self.in_dim, self.h_dim * 20, bias=True)  # class initialization
        hid_lay = nn.Linear(self.h_dim * 20, self.h_dim * 20, bias=True)
        hid_lay_2 = nn.Linear(self.h_dim * 20, self.h_dim * 20, bias=True)
        out_lay = nn.Linear(self.h_dim * 20, self.out_dim, bias=True)
        self.net = nn.Sequential(in_lay,
                                 nn.Sigmoid(),
                                 hid_lay,
                                 nn.LeakyReLU(),
                                 hid_lay_2,
                                 nn.LeakyReLU(),
                                 out_lay)

        # evaluation standards
        self.criterion = nn.MSELoss()  # class initialization

        # optimizer
        self.optim = optim.Adam(self.net.parameters(), lr=1e-3, betas=(0.9, 0.99))

        # print network architecture
        print_network('demo', self.net)
        # print_net_parameters(self.net, OrderedDict(), title='Initialization parameters')

    def forward(self, X):
        o1 = self.net(X)

        return o1

    def train(self, train_set):
        print('training')
        # X,y = train_set
        # train_set = (torch.from_numpy(X).double(), torch.from_numpy(y).double())
        train_loader = Data.DataLoader(train_set, 50, shuffle=True, num_workers=4)
        all_params_order_dict = OrderedDict()

        ith_layer_out_dict = OrderedDict()

        loss_lst = []
        epochs = 10
        for epoch in range(epochs):
            param_order_dict = OrderedDict()
            loss_tmp = torch.Tensor([0.0])
            for i, (b_x, b_y) in enumerate(train_loader):
                b_x = b_x.view([b_x.shape[0], -1]).float()
                b_y = b_y.view(b_y.shape[0], 1).float()

                self.optim.zero_grad()
                b_y_preds = self.forward(b_x)
                loss = self.criterion(b_y_preds, b_y)
                print('%d/%d, batch_ith = %d, loss=%f' % (epoch, epochs, i, loss.data))
                loss.backward()
                self.optim.step()

                loss_tmp += loss.data
                # for idx, param in enumerate(self.net.parameters()):
                for name, param in self.net.named_parameters():
                    # print(name, param)  # even is weigh and bias, odd is activation function, it's no parameters.
                    if name not in param_order_dict.keys():
                        param_order_dict[name] = copy.deepcopy(param.data.numpy())  # numpy arrary
                    else:
                        # param_order_dict[name].append(copy.deepcopy(np.reshape(param.data.numpy(), (-1, 1))))
                        param_order_dict[name] += copy.deepcopy(param.data.numpy())  # numpy arrary
            loss_lst.append(loss_tmp.data / len(train_loader))
            if epoch not in all_params_order_dict.keys():  # key = epoch, value =param_order_dict
                # average parameters
                all_params_order_dict[epoch] = {key: value / len(train_loader) for key, value in
                                                param_order_dict.items()}

        if self.display_flg:
            plot_data(loss_lst, x_label='epochs', y_label='loss', title='training model')
            live_plot_params(self.net, all_params_order_dict, output_file='dynamic.mp4')

        print_net_parameters(self.net, param_order_dict,
                             title='All parameters (weights and bias) from \n begin to finish in training process phase.')

        print_net_parameters(self.net, OrderedDict(), title='Final parameters')


def plot_data(data, x_label, y_label, title=''):
    r"""

    :param data:
    :param x_label:
    :param y_label:
    :param title:
    :return:
    """
    # recommend to use, plt.subplots() default parameter is (111)
    fig, ax = plt.subplots()  # combine plt.figure and fig.add_subplots(111)
    ax.plot(data)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    # ax.set_ylabel()
    plt.show()


def live_plot_params(net, all_params_order_dict, output_file='dynamic.mp4'):
    r"""
        save the change of parameters in each epcoh to .mp4 file

        must install ffmpeg, then pip3 install ffmpeg
        Note:
            pycharm cannot show animation. so it needs to save animation to local file.

    :param net:  neural network based on pytorch
    :param all_params_order_dict:
    :param output_file:
    :return:
    """
    num_figs = len(net) // 2 + 1  # number of layers in nn
    fig, axes = plt.subplots(nrows=num_figs, ncols=2)  # create fig and add subplots (axes) into it.
    ax_lst = []

    def update(frame_data):
        ith_epoch, ith_param_order_dict = frame_data  # dictionary
        fontsize = 7
        for ax_i, (key, value) in zip(axes.flatten(), ith_param_order_dict.items()):
            ax_i.clear()  # clear the previous data, then redraw the new data.
            num_bins = value.size // 2
            if num_bins < 10:
                num_bins = 10
            print('epoch=%s, key=%s' % (ith_epoch, key))
            y_tmp = np.reshape(np.asarray(value, dtype=float), (-1, 1))
            # n, bins, patches = ax_i.hist(np.reshape(np.asarray(value, dtype=float), (-1, 1)), num_bins,
            #                              facecolor='blue', alpha=0.5)
            ax_i.scatter(range(value.size), y_tmp, c=y_tmp, s=2)
            ax_i.set_xlabel('Values', fontsize=fontsize)
            ax_i.set_ylabel('Frequency', fontsize=fontsize)
            # ax_i.set_xticks(range(6))
            # ax_i.set_xticklabels([str(x) + "foo" for x in range(6)], rotation=45, fontsize=fontsize)
            # ax_i.set_xticklabels(ax_i.get_xticks(),fontsize=fontsize)
            for label in (ax_i.get_xticklabels() + ax_i.get_yticklabels()):
                label.set_fontname('Arial')
                label.set_fontsize(fontsize)
            # ax_i.set_xlim(-1,1)
            # ax_i.set_ylim(0,value.size)
            ax_i.set_title('%s:(%s^T)' % (key, value.shape), fontsize=fontsize)  # paramter_name and shape
        fig.suptitle('epoch:%d' % ith_epoch)

        return ax_lst

    def new_data():
        for ith_epoch, ith_param_order_dict in all_params_order_dict.items():
            print('epoch(%d)/epochs(%d)' % (ith_epoch, len(all_params_order_dict.keys())))
            yield ith_epoch, ith_param_order_dict

    fig.tight_layout(rect=[0, 0.03, 1, 0.95])  # rect: tuple (left, bottom, right, top), optional
    # tight_layout(pad=0.05, w_pad=0.001, h_pad=2.0)
    # fig.subplots_adjust(top=0.88)
    anim = FuncAnimation(fig, update, frames=new_data, repeat=False, interval=1000,
                         blit=False)  # interval : ms
    anim.save(output_file, writer='ffmpeg', fps=None, dpi=400)
    plt.show()


def print_net_parameters(net, param_order_dict=OrderedDict(), title=''):
    r"""

    :param net:
    :param param_order_dict:
    :param title:
    :return:
    """
    num_figs = len(net) // 2 + 1
    print('subplots:(%dx%d):' % (num_figs, num_figs))
    print(title)
    if param_order_dict == {}:
        # for idx, param in enumerate(self.net.parameters()):
        for name, param in net.named_parameters():
            print(name, param)  # even is weigh and bias, odd is activation function, it's no parameters.
            if name not in param_order_dict.keys():
                param_order_dict[name] = copy.deepcopy(np.reshape(param.data.numpy(), (-1, 1)))
            else:
                print('error:', name)

    fig, axes = plt.subplots(nrows=num_figs, ncols=2)
    fontsize = 10
    # plt.suptitle(title, fontsize=8)
    x_label = 'Values'
    y_label = 'Frequency'
    for ith, (ax_i, (name, param)) in enumerate(zip(axes.flatten(), net.named_parameters())):
        # for ith, (name, param) in enumerate(net.named_parameters()):
        print('subplot_%dth' % (ith + 1))
        num_bins = 10
        x_tmp = np.reshape(np.asarray(param_order_dict[name], dtype=float), (-1, 1))
        n, bins, patches = ax_i.hist(x_tmp, num_bins, facecolor='blue', alpha=0.5)
        ax_i.set_xlabel('Values', fontsize=fontsize)
        ax_i.set_ylabel('Frequency', fontsize=fontsize)
        ax_i.set_title('%s:(%s^T)' % (name, param.data.numpy().shape), fontsize=fontsize)  # paramter_name and shape
    fig.suptitle(title, fontsize=fontsize)
    fig.tight_layout(rect=[0, 0.03, 1, 0.90])  # rect: tuple (left, bottom, right, top), optional
    # plt.tight_layout()
    # plt.subplots_adjust(top=0.88)
    plt.show()


# def show_figures(D_loss, G_loss):
#     import matplotlib.pyplot as plt
#     fig, axes=plt.subplots(111)
#
#     plt.plot(D_loss, 'r', alpha=0.5, label='D_loss of real and fake sample')
#     plt.plot(G_loss, 'g', alpha=0.5, label='D_loss of G generated fake sample')
#     plt.legend(loc='upper right')
#     plt.title('D\'s loss of real and fake sample.')
#     plt.show()

if __name__ == '__main__':
    train_set = generated_train_set(100)
    nn_demo = NerualNetworkDome()
    nn_demo.train(train_set)

    # dynamic_plot(input_f="/home/kun/PycharmProjects/MachineLearning_Studying/data/attack_demo.csv")