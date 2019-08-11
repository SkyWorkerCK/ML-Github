import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data
import mnist_forward
import os

BATCH_SIZE = 100
LEARNING_RATE_BASE = 0.2      # 初始学习率
LEARNING_RATE_DECAY = 0.95    # 学习衰减率
REGULARIZER = 0.0005          # 正则率
STEPS = 150000                # 训练轮数
MOVING_AVERAGE_DECAY = 0.99   # 滑动平均衰减率
MODEL_SAVE_PATH = "./model/"  # 模型保存路径
MODEL_NAME = "mnist_model"    # 模型名称

def backward(mnist):
    x = tf.placeholder(tf.float32, [None, mnist_forward.INPUT_NODE])
    y_ = tf.placeholder(tf.float32, [None, mnist_forward.OUTPUT_NODE])
    # 正向传输推算出模型
    y = mnist_forward.forward(x, REGULARIZER)
    global_step = tf.Variable(0, trainable=False)

    # 下面算出包括正则化的损失函数
    # logits为神经网络输出层的输出
    # 传入的label为一个一维的vector，长度等于batch_size，每一个值的取值区间必须是[0，num_classes)，其实每一个值就是代表了batch中对应样本的类别
    # tf.argmax(vector, 1)：返回的是vector中的最大值的索引号，axis=0表示列，axis=1表示行
    # 分类问题多用交叉熵作为损失函数
    # 相对MSE而言，曲线整体呈单调性，loss越大，梯度越大。便于梯度下降反向传播，利于优化。所以一般针对分类问题采用交叉熵作为loss函数
    ce = tf.nn.sparse_softmax_cross_entropy_with_logits(logits=y, labels=tf.argmax(y_, 1))
    # 矩阵中所有元素求平均值
    # tf.reduce_mean(x):就是求所有元素的平均值
    # tf.reduce_mean(x,0):就是求维度为0的平均值，也就是求列平均
    # tf.reduce_mean(x,1)：就是求维度为1的平均值，也就是求行平均
    cem = tf.reduce_mean(ce)
    # tf.get_collection(‘losses’)：返回名称为losses的列表
    # tf.add_n(list)：将列表元素相加并返回
    loss = cem + tf.add_n(tf.get_collection('losses'))



    # 定义指数衰减学习率
    learning_rate = tf.train.exponential_decay(
        LEARNING_RATE_BASE,
        global_step,
        mnist.train.num_examples / BATCH_SIZE,
        LEARNING_RATE_DECAY,
        staircase=True
    )


    # 定义训练过程
    train_step = tf.train.GradientDescentOptimizer(learning_rate).minimize(loss, global_step=global_step)


    # 定义滑动平均
    # tf.train.ExponentialMovingAverage()这个函数用于更新参数，就是采用滑动平均的方法更新参数
    # MOVING_AVERAGE_DECAY是衰减率,用于控制模型的更新速度,设置为接近1的值比较合理
    ema = tf.train.ExponentialMovingAverage(MOVING_AVERAGE_DECAY, global_step)
    # apply()方法添加了训练变量的影子副本
    # 影子变量计算方法：shadow_variable=decay⋅shadow_variable+(1−decay)⋅variable
    # 返回值：ExponentialMovingAverage对象，通过对象调用apply方法可以通过滑动平均模型来更新参数。
    # tf.trainable_variables返回的是需要训练的变量列表
    # tf.all_variables返回的是所有变量的列表
    ema_op = ema.apply(tf.trainable_variables())
    with tf.control_dependencies([train_step, ema_op]):
        # 里面的内容需要在将train_step、ema_op执行完后才能执行
        # tf.no_op()表示执行完 train_step, ema_op 操作之后什么都不做
        train_op = tf.no_op(name='train')

    saver = tf.train.Saver()

    with tf.Session() as sess:
        # 初始化所有变量
        init_op = tf.global_variables_initializer()
        sess.run(init_op)

        # 通过设置ckpt实现断点续训的功能
        ckpt = tf.train.get_checkpoint_state(MODEL_SAVE_PATH)
        if ckpt and ckpt.model_checkpoint_path:
            saver.restore(sess, ckpt.model_checkpoint_path)

        for i in range(STEPS):
            xs, ys = mnist.train.next_batch(BATCH_SIZE)
            # xs= (100, 784)
            # ys= (100, 10)
            _, loss_value, step = sess.run([train_op, loss, global_step], feed_dict={x: xs, y_: ys})
            if i % 1000 == 0:
                # 计算准确率
                correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(y_, 1))
                # tf.reduce_mean 函数用于计算张量tensor沿着指定的数轴（tensor的某一维度）上的的平均值
                accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
                accuracy_score = sess.run(accuracy, feed_dict={x: mnist.test.images, y_: mnist.test.labels})
                print("After %s training step(s), test accuracy = %g" % (step, accuracy_score))
                # print("After %d training step(s) , loss on training batch is %g." % (step, loss_value))
                saver.save(sess, os.path.join(MODEL_SAVE_PATH, MODEL_NAME), global_step=global_step)


def main():
    mnist = input_data.read_data_sets("./MNIST-data", one_hot=True)
    backward(mnist)

if __name__ == '__main__':
    main()
    # BATCH_SIZE = 200
    # mnist = input_data.read_data_sets("./MNIST-data", one_hot=True)
    # xs, ys = mnist.train.next_batch(BATCH_SIZE)
    # print("xs=", xs.shape)
    # print("ys=", ys.shape)