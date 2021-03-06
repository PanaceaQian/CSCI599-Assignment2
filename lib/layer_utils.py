import numpy as np


def sigmoid(x):
    """
    A numerically stable version of the logistic sigmoid function.
    """
    pos_mask = (x >= 0)
    neg_mask = (x < 0)
    z = np.zeros_like(x)
    z[pos_mask] = np.exp(-x[pos_mask])
    z[neg_mask] = np.exp(x[neg_mask])
    top = np.ones_like(x)
    top[neg_mask] = z[neg_mask]
    return top / (1 + z)


class RNN(object):
    def __init__(self, *args):
        """
        RNN Object to serialize the NN layers
        Please read this code block and understand how it works
        """
        self.params = {}
        self.grads = {}
        self.layers = []
        self.paramName2Indices = {}
        self.layer_names = {}

        # process the parameters layer by layer
        layer_cnt = 0
        for layer in args:
            for n, v in layer.params.items():
                if v is None:
                    continue
                self.params[n] = v
                self.paramName2Indices[n] = layer_cnt
            for n, v in layer.grads.items():
                self.grads[n] = v
            if layer.name in self.layer_names:
                raise ValueError("Existing name {}!".format(layer.name))
            self.layer_names[layer.name] = True
            self.layers.append(layer)
            layer_cnt += 1
        layer_cnt = 0

    def assign(self, name, val):
        # load the given values to the layer by name
        layer_cnt = self.paramName2Indices[name]
        self.layers[layer_cnt].params[name] = val

    def assign_grads(self, name, val):
        # load the given values to the layer by name
        layer_cnt = self.paramName2Indices[name]
        self.layers[layer_cnt].grads[name] = val

    def get_params(self, name):
        # return the parameters by name
        return self.params[name]

    def get_grads(self, name):
        # return the gradients by name
        return self.grads[name]

    def gather_params(self):
        """
        Collect the parameters of every submodules
        """
        for layer in self.layers:
            for n, v in layer.params.iteritems():
                self.params[n] = v

    def gather_grads(self):
        """
        Collect the gradients of every submodules
        """
        for layer in self.layers:
            for n, v in layer.grads.iteritems():
                self.grads[n] = v

    def load(self, pretrained):
        """ 
        Load a pretrained model by names 
        """
        for layer in self.layers:
            if not hasattr(layer, "params"):
                continue
            for n, v in layer.params.iteritems():
                if n in pretrained.keys():
                    layer.params[n] = pretrained[n].copy()
                    print("Loading Params: {} Shape: {}".format(n, layer.params[n].shape))


class VanillaRNN(object):
    def __init__(self, input_dim, h_dim, init_scale=0.02, name='vanilla_rnn'):
        """
        In forward pass, please use self.params for the weights and biases for this layer
        In backward pass, store the computed gradients to self.grads
        - name: the name of current layer
        - input_dim: input dimension
        - h_dim: hidden state dimension
        - meta: to store the forward pass activations for computing backpropagation 
        """
        self.name = name
        self.wx_name = name + "_wx"
        self.wh_name = name + "_wh"
        self.b_name = name + "_b"
        self.input_dim = input_dim
        self.h_dim = h_dim
        self.params = {}
        self.grads = {}
        self.params[self.wx_name] = init_scale * np.random.randn(input_dim, h_dim)
        self.params[self.wh_name] = init_scale * np.random.randn(h_dim, h_dim)
        self.params[self.b_name] = np.zeros(h_dim)
        self.grads[self.wx_name] = None
        self.grads[self.wh_name] = None
        self.grads[self.b_name] = None
        self.meta = None
        
    def step_forward(self, x, prev_h):
        """
        x: input feature (N, D)
        prev_h: hidden state from the previous timestep (N, H)

        meta: variables needed for the backward pass
        """
        next_h, meta = None, None
        assert np.prod(x.shape[1:]) == self.input_dim, "But got {} and {}".format(
            np.prod(x.shape[1:]), self.input_dim)
        ############################################################################
        # TODO: implement forward pass of a single timestep of a vanilla RNN.      #
        # Store the results in the variable output provided above as well as       #
        # values needed for the backward pass.                                     #
        ############################################################################
        # h(t) = tanh(U * x + W * h(t-1) + b)
        next_h = np.tanh(np.dot(x, self.params[self.wx_name]) + np.dot(prev_h, self.params[self.wh_name]) + self.params[self.b_name])
        meta = [x, prev_h, next_h]
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        return next_h, meta

    def step_backward(self, dnext_h, meta):
        """
        dnext_h: gradient w.r.t. next hidden state
        meta: variables needed for the backward pass

        dx: gradients of input feature (N, D)
        dprev_h: gradients of previous hiddel state (N, H)
        dWh: gradients w.r.t. feature-to-hidden weights (H, H)
        dWx: gradients w.r.t. hidden-to-hidden weights (D, H)
        db: gradients w.r.t bias (H,)
        """
        dx, dprev_h, dWx, dWh, db = None, None, None, None, None
        #############################################################################
        # TODO: Implement the backward pass of a single timestep of a vanilla RNN.  #
        # Store the computed gradients for current layer in self.grads with         #
        # corresponding name.                                                       # 
        #############################################################################
        x, prev_h, next_h = meta
        dtanh = dnext_h * (1 - next_h ** 2) # (N, H)
        
        dx = np.dot(dtanh, self.params[self.wx_name].T) # (N, H)*(H, D) -> (N, D)
        dWx = np.dot(x.T, dtanh) # (D, N) * (N, H) -> (D, H)
        
        dprev_h = np.dot(dtanh, self.params[self.wh_name].T) # (N, H)*(H, H) -> (N, H)
        dWh = np.dot(prev_h.T, dtanh) # (H, N)*(N, H) -> (H, H)
        
        db = np.sum(dtanh, axis=0)
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        return dx, dprev_h, dWx, dWh, db

    def forward(self, x, h0):
        """
        x: input feature for the entire timeseries (N, T, D)
        h0: initial hidden state (N, H)
        """
        h = None
        self.meta = []
        ##############################################################################
        # TODO: Implement forward pass for a vanilla RNN running on a sequence of    #
        # input data. You should use the step_forward function that you defined      #
        # above. You can use a for loop to help compute the forward pass.            #
        ##############################################################################
        (N, T, D), H = x.shape, self.h_dim
        h = np.zeros((N, T, H)) # h: initial hidden states(N, T, H)
        
        for t in range(T):
            if t == 0:
                h[:, t, :], meta_t = self.step_forward(x[:, t, :], h0)
            else:
                h[:, t, :], meta_t = self.step_forward(x[:, t, :], h[:, t-1, :])
            self.meta.append(meta_t)
        ##############################################################################
        #                               END OF YOUR CODE                             #
        ##############################################################################
        return h

    def backward(self, dh):
        """
        dh: gradients of hidden states for the entire timeseries (N, T, H)

        dx: gradient of inputs (N, T, D)
        dh0: gradient w.r.t. initial hidden state (N, H)
        self.grads[self.wx_name]: gradient of input-to-hidden weights (D, H)
        self.grads[self.wh_name]: gradient of hidden-to-hidden weights (H, H)
        self.grads[self.b_name]: gradient of biases (H,)
        """
        dx, dh0 = None, None
        self.grads[self.wx_name] = None
        self.grads[self.wh_name] = None
        self.grads[self.b_name] = None
        ##############################################################################
        # TODO: Implement the backward pass for a vanilla RNN running an entire      #
        # sequence of data. You should use the rnn_step_backward function that you   #
        # defined above. You can use a for loop to help compute the backward pass.   #
        # HINT: Gradients of hidden states come from two sources                     #
        ##############################################################################
        (N, T, H), D = dh.shape, self.input_dim
        
        dx = np.zeros((N, T, D))
        self.grads[self.wx_name] = np.zeros((D, H)) 
        self.grads[self.wh_name] = np.zeros((H, H))
        self.grads[self.b_name] = np.zeros((H, ))
        
        dnext_h = dh[:, T-1, :]
        
        # print("N, T, H, D is {}, {}, {}, {}".format(N, T, D, H))
        # print("meta shape is {}".format(len(self.meta)))
        
        for t in range(T-1, -1, -1):            
            dx_i, dprev_h_i, dWx_i, dWh_i, db_i = self.step_backward(dnext_h, self.meta[t])
            dx[:, t, :] = dx_i
            
            if t == 0:
                dh0 = dprev_h_i
            else:
                dnext_h = dprev_h_i + dh[:, t-1, :]
            
            self.grads[self.wx_name] += dWx_i
            self.grads[self.wh_name] += dWh_i
            self.grads[self.b_name] += db_i
            
        ##############################################################################
        #                               END OF YOUR CODE                             #
        ##############################################################################
        self.meta = []
        return dx, dh0


class LSTM(object):
    def __init__(self, input_dim, h_dim, init_scale=0.02, name='lstm'):
        """
        In forward pass, please use self.params for the weights and biases for this layer
        In backward pass, store the computed gradients to self.grads
        - name: the name of current layer
        - input_dim: input dimension
        - h_dim: hidden state dimension
        - meta: to store the forward pass activations for computing backpropagation 
        """
        self.name = name
        self.wx_name = name + "_wx"
        self.wh_name = name + "_wh"
        self.b_name = name + "_b"
        self.input_dim = input_dim
        self.h_dim = h_dim
        self.params = {}
        self.grads = {}
        self.params[self.wx_name] = init_scale * np.random.randn(input_dim, 4*h_dim)
        self.params[self.wh_name] = init_scale * np.random.randn(h_dim, 4*h_dim)
        self.params[self.b_name] = np.zeros(4*h_dim)
        self.grads[self.wx_name] = None
        self.grads[self.wh_name] = None
        self.grads[self.b_name] = None
        self.meta = None
        
    def step_forward(self, x, prev_h, prev_c):
        """
        x: input feature (N, D)
        prev_h: hidden state from the previous timestep (N, H)

        meta: variables needed for the backward pass
        """
        next_h, next_c, meta = None, None, None
        #############################################################################
        # TODO: Implement the forward pass for a single timestep of an LSTM.        #
        # You may want to use the numerically stable sigmoid implementation above.  #
        #############################################################################
        # Xt: (N, D); Wx: (D, 4H); Wh: (H, 4H); prev_h: (N, H); A = Xt*Wx + Ht-1*Wh + b : (N, 4H)
        A = np.dot(x, self.params[self.wx_name]) + np.dot(prev_h, self.params[self.wh_name]) + self.params[self.b_name]
        H = self.h_dim
        [a_i, a_f, a_o, a_g] = [A[:, (i*H):((i+1)*H)] for i in range(4)]
        i, f, o, g = sigmoid(a_i), sigmoid(a_f), sigmoid(a_o), np.tanh(a_g)
        
        # ct = f * ct-1 + i * g while *=element-wise product
        next_c = np.multiply(f, prev_c) + np.multiply(i, g)
        # ht = o * tanh(ct) while *=element-wise product
        next_h = np.multiply(o, np.tanh(next_c))
        
        meta = [x, prev_h, prev_c, i, f, o, g, next_c, next_h]        
        #############################################################################
        #                               END OF YOUR CODE                            #
        #############################################################################
        return next_h, next_c, meta
        
    def step_backward(self, dnext_h, dnext_c, meta):
        """
        dnext_h: gradient w.r.t. next hidden state, (N, H)
        meta: variables needed for the backward pass

        dx: gradients of input feature (N, D)
        dprev_h: gradients of previous hiddel state (N, H)
        dWh: gradients w.r.t. feature-to-hidden weights (D, H)
        dWx: gradients w.r.t. hidden-to-hidden weights (H, H)
        db: gradients w.r.t bias (H,)
        """
        dx, dh, dc, dWx, dWh, db = None, None, None, None, None, None
        #############################################################################
        # TODO: Implement the backward pass for a single timestep of an LSTM.       #
        #                                                                           #
        # HINT: For sigmoid and tanh you can compute local derivatives in terms of  #
        # the output value from the nonlinearity.                                   #
        #############################################################################
        # Reference: http://arunmallya.github.io/writeups/nn/lstm/index.html#/8
        x, prev_h, prev_c, i, f, o, g, next_c, next_h = meta
        
        # do, dc
        do = dnext_h * np.tanh(next_c)
        dtanh_c = dnext_h * o
        
        dnext_c += dtanh_c * (1 - np.tanh(next_c) ** 2)
        
        # df, di, dg, dprev_c
        di = dnext_c * g
        df = dnext_c * prev_c
        dprev_c = dnext_c * f
        dg = dnext_c * i
        
        # d_af, d_ai, d_ag, d_ao, dA
        d_af = df * f * (1 - f)
        d_ai = di * i * (1 - i)
        d_ao = do * o * (1 - o)
        d_ag = dg * (1 - g ** 2)
        
        N, H = dnext_h.shape
        # print ("N, H is {}, {}".format(N, H))
        # print ("dai, daf, dao, dag shape is {}, {}, {}, {}".format(d_ai.shape, d_af.shape, d_ao.shape, d_ag.shape))
        dA = np.zeros((N, 4 * H))
        dA[:, 0:H] += d_ai
        dA[:, H:2*H] += d_af
        dA[:, 2*H:3*H] += d_ao
        dA[:, 3*H:4*H] += d_ag
        
        # dWh, dWx, dx, db, dh
        # Xt: (N, D); Wx: (D, 4H); Wh: (H, 4H); prev_h: (N, H); A = Xt*Wx + Ht-1*Wh + b : (N, 4H)
        dWh = np.dot(prev_h.T, dA)
        dWx = np.dot(x.T, dA)
        dx = np.dot(dA, self.params[self.wx_name].T)
        dprev_h = np.dot(dA, self.params[self.wh_name].T)
        db = np.sum(dA, axis=0)
        #############################################################################
        #                               END OF YOUR CODE                            #
        #############################################################################

        return dx, dprev_h, dprev_c, dWx, dWh, db

    def forward(self, x, h0):
        """
        Forward pass for an LSTM over an entire sequence of data. We assume an input
        sequence composed of T vectors, each of dimension D. The LSTM uses a hidden
        size of H, and we work over a minibatch containing N sequences. After running
        the LSTM forward, we return the hidden states for all timesteps.

        Note that the initial cell state is passed as input, but the initial cell
        state is set to zero. Also note that the cell state is not returned; it is
        an internal variable to the LSTM and is not accessed from outside.

        Inputs:
        - x: Input data of shape (N, T, D)
        - h0: Initial hidden state of shape (N, H)
        - Wx: Weights for input-to-hidden connections, of shape (D, 4H)
        - Wh: Weights for hidden-to-hidden connections, of shape (H, 4H)
        - b: Biases of shape (4H,)

        Returns a tuple of:
        - h: Hidden states for all timesteps of all sequences, of shape (N, T, H)
        - cache: Values needed for the backward pass.
        """
        h = None
        self.meta = []
        #############################################################################
        # TODO: Implement the forward pass for an LSTM over an entire timeseries.   #
        # You should use the lstm_step_forward function that you just defined.      #
        #############################################################################
        (N, T, D), H = x.shape, self.h_dim
        h = np.zeros((N, T, H)) # h: initial hidden states(N, T, H)
        c = np.zeros((N, T, H))
        c0 = np.zeros(h0.shape)
        
        for t in range(T):
            if t == 0:
                h[:, t, :], c[:, t, :], meta_t = self.step_forward(x[:, t, :], h0, c0)
            else:
                h[:, t, :], c[:, t, :], meta_t = self.step_forward(x[:, t, :], h[:, t-1, :], c[:, t-1, :])
            self.meta.append(meta_t)
        #############################################################################
        #                               END OF YOUR CODE                            #
        #############################################################################
        return h

    def backward(self, dh):
        """
        Backward pass for an LSTM over an entire sequence of data.]

        Inputs:
        - dh: Upstream gradients of hidden states, of shape (N, T, H)
        - cache: Values from the forward pass

        Returns a tuple of:
        - dx: Gradient of input data of shape (N, T, D)
        - dh0: Gradient of initial hidden state of shape (N, H)
        - dWx: Gradient of input-to-hidden weight matrix of shape (D, 4H)
        - dWh: Gradient of hidden-to-hidden weight matrix of shape (H, 4H)
        - db: Gradient of biases, of shape (4H,)
        """
        dx, dh0 = None, None
        #############################################################################
        # TODO: Implement the backward pass for an LSTM over an entire timeseries.  #
        # You should use the lstm_step_backward function that you just defined.     #
        #############################################################################
        (N, T, H), D = dh.shape, self.input_dim
        
        dx = np.zeros((N, T, D))
        dc = np.zeros(dh.shape)
        self.grads[self.wx_name] = np.zeros((D, 4*H)) 
        self.grads[self.wh_name] = np.zeros((H, 4*H))
        self.grads[self.b_name] = np.zeros((4*H, ))
        
        dnext_h = dh[:, T-1, :]
        dnext_c = dc[:, T-1, :]
        
        for t in range(T-1, -1, -1):            
            dx_i, dprev_h_i, dprev_c_i, dWx_i, dWh_i, db_i = self.step_backward(dnext_h, dnext_c, self.meta[t])
            dx[:, t, :] = dx_i
            
            if t == 0:
                dh0 = dprev_h_i
            else:
                dnext_h = dprev_h_i + dh[:, t-1, :]
                dnext_c = dprev_c_i + dc[:, t-1, :]
            
            self.grads[self.wx_name] += dWx_i
            self.grads[self.wh_name] += dWh_i
            self.grads[self.b_name] += db_i
        #############################################################################
        #                               END OF YOUR CODE                            #
        #############################################################################
        self.meta = []
        return dx, dh0
            
        
class word_embedding(object):
    def __init__(self, voc_dim, vec_dim, name="we"):
        """
        In forward pass, please use self.params for the weights and biases for this layer
        In backward pass, store the computed gradients to self.grads
        - name: the name of current layer
        - v_dim: words size
        - output_dim: vector dimension
        - meta: to store the forward pass activations for computing backpropagation
        """
        self.name = name
        self.w_name = name + "_w"
        self.voc_dim = voc_dim
        self.vec_dim = vec_dim
        self.params = {}
        self.grads = {}
        self.params[self.w_name] = np.random.randn(voc_dim, vec_dim)
        self.grads[self.w_name] = None
        self.meta = None
        
    def forward(self, x):
        """
        Forward pass for word embeddings. We operate on minibatches of size N where
        each sequence has length T. We assume a vocabulary of V words, assigning each
        to a vector of dimension D.

        Inputs:
        - x: Integer array of shape (N, T) giving indices of words. Each element idx
          of x muxt be in the range 0 <= idx < V.
        - W: Weight matrix of shape (V, D) giving word vectors for all words.

        Returns a tuple of:
        - out: Array of shape (N, T, D) giving word vectors for all input words.
        - meta: Values needed for the backward pass
        """
        out, self.meta = None, None
        ##############################################################################
        # TODO: Implement the forward pass for word embeddings.                      #
        #                                                                            #
        # HINT: This can be done in one line using NumPy's array indexing.           #
        ##############################################################################
        out = self.params[self.w_name][x, :]
        self.meta = [out, x]        
        ##############################################################################
        #                               END OF YOUR CODE                             #
        ##############################################################################
        return out
        
    def backward(self, dout):
        """
        Backward pass for word embeddings. We cannot back-propagate into the words
        since they are integers, so we only return gradient for the word embedding
        matrix.

        HINT: Look up the function np.add.at

        Inputs:
        - dout: Upstream gradients of shape (N, T, D)
        - cache: Values from the forward pass

        Returns:
        - dW: Gradient of word embedding matrix, of shape (V, D).
        """
        self.grads[self.w_name] = None
        ##############################################################################
        # TODO: Implement the backward pass for word embeddings.                     #
        # Note that Words can appear more than once in a sequence.                   #
        # HINT: Look up the function np.add.at                                       #
        ##############################################################################
        out, x = self.meta
        self.grads[self.w_name] = np.zeros(self.params[self.w_name].shape)
        np.add.at(self.grads[self.w_name], x, dout)
        ##############################################################################
        #                               END OF YOUR CODE                             #
        ##############################################################################


class temporal_fc(object):
    def __init__(self, input_dim, output_dim, init_scale=0.02, name='t_fc'):
        """
        In forward pass, please use self.params for the weights and biases for this layer
        In backward pass, store the computed gradients to self.grads
        - name: the name of current layer
        - input_dim: input dimension
        - output_dim: output dimension
        - meta: to store the forward pass activations for computing backpropagation 
        """
        self.name = name
        self.w_name = name + "_w"
        self.b_name = name + "_b"
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.params = {}
        self.grads = {}
        self.params[self.w_name] = init_scale * np.random.randn(input_dim, output_dim)
        self.params[self.b_name] = np.zeros(output_dim)
        self.grads[self.w_name] = None
        self.grads[self.b_name] = None
        self.meta = None
        
    def forward(self, x):
        """
        Forward pass for a temporal fc layer. The input is a set of D-dimensional
        vectors arranged into a minibatch of N timeseries, each of length T. We use
        an affine function to transform each of those vectors into a new vector of
        dimension M.

        Inputs:
        - x: Input data of shape (N, T, D)
        - w: Weights of shape (D, M)
        - b: Biases of shape (M,)

        Returns a tuple of:
        - out: Output data of shape (N, T, M)
        - cache: Values needed for the backward pass
        """
        N, T, D = x.shape
        M = self.params[self.b_name].shape[0]
        out = x.reshape(N * T, D).dot(self.params[self.w_name]).reshape(N, T, M) + self.params[self.b_name]
        self.meta = [x, out]
        return out

    def backward(self, dout):
        """
        Backward pass for temporal fc layer.

        Input:
        - dout: Upstream gradients of shape (N, T, M)
        - cache: Values from forward pass

        Returns a tuple of:
        - dx: Gradient of input, of shape (N, T, D)
        - dw: Gradient of weights, of shape (D, M)
        - db: Gradient of biases, of shape (M,)
        """
        x, out = self.meta
        N, T, D = x.shape
        M = self.params[self.b_name].shape[0]

        dx = dout.reshape(N * T, M).dot(self.params[self.w_name].T).reshape(N, T, D)
        self.grads[self.w_name] = dout.reshape(N * T, M).T.dot(x.reshape(N * T, D)).T
        self.grads[self.b_name] = dout.sum(axis=(0, 1))

        return dx


class temporal_softmax_loss(object):
    def __init__(self, dim_average=True):
        """
        - dim_average: if dividing by the input dimension or not
        - dLoss: intermediate variables to store the scores
        - label: Ground truth label for classification task
        """
        self.dim_average = dim_average  # if average w.r.t. the total number of features
        self.dLoss = None
        self.label = None

    def forward(self, feat, label, mask):
        """ Some comments """
        loss = None
        N, T, V = feat.shape

        feat_flat = feat.reshape(N * T, V)
        label_flat = label.reshape(N * T)
        mask_flat = mask.reshape(N * T)

        probs = np.exp(feat_flat - np.max(feat_flat, axis=1, keepdims=True))
        probs /= np.sum(probs, axis=1, keepdims=True)
        loss = -np.sum(mask_flat * np.log(probs[np.arange(N * T), label_flat]))
        if self.dim_average:
            loss /= N

        self.dLoss = probs.copy()
        self.label = label
        self.mask = mask
        
        return loss

    def backward(self):
        N, T = self.label.shape
        dLoss = self.dLoss
        if dLoss is None:
            raise ValueError("No forward function called before for this module!")
        dLoss[np.arange(dLoss.shape[0]), self.label.reshape(N * T)] -= 1.0
        if self.dim_average:
            dLoss /= N
        dLoss *= self.mask.reshape(N * T)[:, None]
        self.dLoss = dLoss
        
        return dLoss.reshape(N, T, -1)
