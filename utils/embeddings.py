import tensorflow as tf
import tensorflow_hub as hub


class UniversalSentenceEncoder(object):
    def __init__(self,
                 module_url="./tensorflow_models/universal_sentence_encoder/",
                 encoder_type="DAN"):
        self.embedding = hub.Module(module_url)
        self.encoder_type = encoder_type

        #  initalize the tensor flow for USE graph
        graph = tf.Graph()
        with graph.as_default():
            # We will be feeding 1D tensors of text into the graph.
            self.text_input = tf.placeholder(
                dtype=tf.string,
                shape=[None])
            embed = hub.Module(module_url)
            self.embedded_text = embed(self.text_input)
            init_op = tf.group(
                [tf.global_variables_initializer(),
                 tf.tables_initializer()])
        graph.finalize()

        self.session = tf.Session(graph=graph)
        self.session.run(init_op)

    def embed(self, sentences=None):
        return self.session.run(
                self.embedded_text,
                feed_dict={self.text_input: sentences.values}
            )
