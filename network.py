import tensorlayer as tl
import tensorflow as tf
import time


def network_g(image_gray, reuse, is_train):
    with tf.variable_scope('network_g', reuse=reuse) as vs:
        tl.layers.set_name_reuse(reuse)
        net = tl.layers.InputLayer(inputs=image_gray, name="input_layer")
        net = tl.layers.Conv2d(net, n_filter=64, filter_size=(3, 3), strides=(1, 1), act=tf.nn.relu, name="pre_conv")
        for i in range(7):
            nn = tl.layers.Conv2d(net, n_filter=64, filter_size=(3, 3), strides=(1, 1), name="res%d/c/1" % i)
            nn = tl.layers.BatchNormLayer(nn, is_train=is_train, name="res%s/b/1" % i)
            nn = tl.layers.PReluLayer(nn, name="res%d/prelu/1" % i)
            # nn = tl.layers.DeConv2d(nn, n_filter=128, filter_size=(3, 3), strides=(2, 2), act=tf.nn.relu, name="res%d/dc" % i)
            # nn = tl.layers.Conv2d(nn, n_filter=128, filter_size=(3, 3), strides=(2, 2), act=tf.nn.relu, name="res%d/dc" % i)
            nn = tl.layers.Conv2d(nn, n_filter=64, filter_size=(3, 3), strides=(1, 1), name="res%d/c/2" % i)
            nn = tl.layers.BatchNormLayer(nn, is_train=is_train, name="res%s/b/2" % i)
            nn = tl.layers.PReluLayer(nn, name="res%d/prelu/2" % i)
            nn = tl.layers.ElementwiseLayer([net, nn], combine_fn=tf.add, name="res%d/add" % i)
            net = nn

        for i in range(4):
            net = tl.layers.Conv2d(net, n_filter=128, filter_size=(3, 3), strides=(2, 2), name="subpixel%d/c" % i)
            net = tl.layers.SubpixelConv2d(net=net, scale=2, act=tf.nn.relu, name='subpixel%d/sub' % i)
            print net.outputs.get_shape()
        net = tl.layers.Conv2d(net, n_filter=64, filter_size=(3, 3), strides=(1, 1), act=tf.nn.relu, name="conv")
        net = tl.layers.Conv2d(net, n_filter=3, filter_size=(3, 3), strides=(1, 1), act=tf.nn.tanh, name="last")
        return net


def network_d(image_input, reuse, is_train):
    with tf.variable_scope('network_d', reuse=reuse) as vs:
        tl.layers.set_name_reuse(reuse)
        net = tl.layers.InputLayer(inputs=image_input, name="input_layer")
        net = tl.layers.Conv2d(net, n_filter=16, filter_size=(3, 3), strides=(2, 2), name="pre/conv")

        net = tl.layers.Conv2d(net, n_filter=16, filter_size=(3, 3), strides=(1, 1), name="b1/c")
        net = tl.layers.BatchNormLayer(net, is_train=is_train, act=tf.nn.relu, name="b1/b")

        net = tl.layers.MaxPool2d(net, filter_size=(3, 3), strides=(2, 2), name="pool1")

        net = tl.layers.Conv2d(net, n_filter=16, filter_size=(3, 3), strides=(1, 1), name="b2/c")
        net = tl.layers.BatchNormLayer(net, is_train=is_train, act=tf.nn.relu, name="b2/b")

        net = tl.layers.Conv2d(net, n_filter=16, filter_size=(3, 3), strides=(1, 1), name="b3/c")
        net = tl.layers.BatchNormLayer( net, is_train=is_train, act=tf.nn.relu, name="b3/b")

        net = tl.layers.MaxPool2d(net, filter_size=(3, 3), strides=(2, 2), name="pool2")

        net = tl.layers.Conv2d(net, n_filter=16, filter_size=(3, 3), strides=(1, 1), name="b4/c")
        net = tl.layers.BatchNormLayer(net, is_train=is_train, act=tf.nn.relu, name="b4/b")

        net = tl.layers.Conv2d(net, n_filter=16, filter_size=(3, 3), strides=(2, 2), name="b5/c")
        net = tl.layers.BatchNormLayer(net, is_train=is_train, act=tf.nn.relu, name="b5/b")

        net = tl.layers.FlattenLayer(net, name="flatten")

        net = tl.layers.DenseLayer(net, n_units=256, act=tf.nn.relu, name="dense512")
        pro = tl.layers.DenseLayer(net, n_units=1, act=tf.nn.relu, name="dense1/p")
        return net, pro


def Vgg19_simple_api(rgb, reuse):
    """
    Build the VGG 19 Model

    Parameters
    -----------
    rgb : rgb image placeholder [batch, height, width, 3] values scaled [0, 1]
    """
    VGG_MEAN = [103.939, 116.779, 123.68]
    with tf.variable_scope("VGG19", reuse=reuse) as vs:
        tl.layers.set_name_reuse(reuse)
        start_time = time.time()
        print("[*] VGG19 model build start...")

        rgb_scaled = rgb * 255.0
        # Convert RGB to BGR
        if tf.__version__ <= '0.11':
            red, green, blue = tf.split(3, 3, rgb_scaled)
        else:  # TF 1.0
            # print(rgb_scaled)
            red, green, blue = tf.split(rgb_scaled, 3, 3)
        assert red.get_shape().as_list()[1:] == [224, 224, 1]
        assert green.get_shape().as_list()[1:] == [224, 224, 1]
        assert blue.get_shape().as_list()[1:] == [224, 224, 1]
        if tf.__version__ <= '0.11':
            bgr = tf.concat(3, [blue - VGG_MEAN[0], green - VGG_MEAN[1], red - VGG_MEAN[2],])
        else:
            bgr = tf.concat([blue - VGG_MEAN[0], green - VGG_MEAN[1], red - VGG_MEAN[2],], axis=3)
        assert bgr.get_shape().as_list()[1:] == [224, 224, 3]
        """ input layer """
        net_in = tl.layers.InputLayer(bgr, name='input')
        """ conv1 """
        network = tl.layers.Conv2d(net_in, n_filter=64, filter_size=(3, 3), strides=(1, 1), act=tf.nn.relu, padding='SAME', name='conv1_1')
        network = tl.layers.Conv2d(network, n_filter=64, filter_size=(3, 3), strides=(1, 1), act=tf.nn.relu,  padding='SAME', name='conv1_2')
        network = tl.layers.MaxPool2d(network, filter_size=(2, 2), strides=(2, 2), padding='SAME', name='pool1')
        """ conv2 """
        network = tl.layers.Conv2d(network, n_filter=128, filter_size=(3, 3), strides=(1, 1), act=tf.nn.relu, padding='SAME', name='conv2_1')
        network = tl.layers.Conv2d(network, n_filter=128, filter_size=(3, 3), strides=(1, 1), act=tf.nn.relu, padding='SAME', name='conv2_2')
        network = tl.layers.MaxPool2d(network, filter_size=(2, 2), strides=(2, 2), padding='SAME', name='pool2')
        """ conv3 """
        network = tl.layers.Conv2d(network, n_filter=256, filter_size=(3, 3), strides=(1, 1), act=tf.nn.relu, padding='SAME', name='conv3_1')
        network = tl.layers.Conv2d(network, n_filter=256, filter_size=(3, 3), strides=(1, 1), act=tf.nn.relu, padding='SAME', name='conv3_2')
        network = tl.layers.Conv2d(network, n_filter=256, filter_size=(3, 3), strides=(1, 1), act=tf.nn.relu, padding='SAME', name='conv3_3')
        network = tl.layers.Conv2d(network, n_filter=256, filter_size=(3, 3), strides=(1, 1), act=tf.nn.relu, padding='SAME', name='conv3_4')
        network = tl.layers.MaxPool2d(network, filter_size=(2, 2), strides=(2, 2), padding='SAME', name='pool3')
        """ conv4 """
        network = tl.layers.Conv2d(network, n_filter=512, filter_size=(3, 3), strides=(1, 1), act=tf.nn.relu, padding='SAME', name='conv4_1')
        network = tl.layers.Conv2d(network, n_filter=512, filter_size=(3, 3), strides=(1, 1), act=tf.nn.relu, padding='SAME', name='conv4_2')
        network = tl.layers.Conv2d(network, n_filter=512, filter_size=(3, 3), strides=(1, 1), act=tf.nn.relu, padding='SAME', name='conv4_3')
        network = tl.layers.Conv2d(network, n_filter=512, filter_size=(3, 3), strides=(1, 1), act=tf.nn.relu, padding='SAME', name='conv4_4')
        network = tl.layers.MaxPool2d(network, filter_size=(2, 2), strides=(2, 2), padding='SAME', name='pool4')  # (batch_size, 14, 14, 512)
        conv = network
        """ conv5 """
        network = tl.layers.Conv2d(network, n_filter=512, filter_size=(3, 3), strides=(1, 1), act=tf.nn.relu, padding='SAME', name='conv5_1')
        network = tl.layers.Conv2d(network, n_filter=512, filter_size=(3, 3), strides=(1, 1), act=tf.nn.relu, padding='SAME', name='conv5_2')
        network = tl.layers.Conv2d(network, n_filter=512, filter_size=(3, 3), strides=(1, 1), act=tf.nn.relu, padding='SAME',  name='conv5_3')
        network = tl.layers.Conv2d(network, n_filter=512, filter_size=(3, 3), strides=(1, 1), act=tf.nn.relu, padding='SAME', name='conv5_4')
        network = tl.layers.MaxPool2d(network, filter_size=(2, 2), strides=(2, 2), padding='SAME', name='pool5')  # (batch_size, 7, 7, 512)
        """ fc 6~8 """
        network = tl.layers.FlattenLayer(network, name='flatten')
        network = tl.layers.DenseLayer(network, n_units=4096, act=tf.nn.relu, name='fc6')
        network = tl.layers.DenseLayer(network, n_units=4096, act=tf.nn.relu, name='fc7')
        network = tl.layers.DenseLayer(network, n_units=1000, act=tf.identity, name='fc8')

        print("[*] model build finished: %fs\n" % (time.time() - start_time))
        return network, conv
