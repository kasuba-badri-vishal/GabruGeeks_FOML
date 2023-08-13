import math
import numpy as np
import pandas as pd

# The seed will be fixed to 42 for this assigmnet.
np.random.seed(42)

NUM_FEATS = 90
FEATURE_SELECTION = False

# Define Activation Function for Softmax
def softmax(y):
    y = y - y.max()
    exp = np.exp(y)
    exp_sum = np.sum(exp,axis=0)
    return exp/exp_sum


def std_scale(X): 
    mean_vec = X.mean(axis= 0)
    std_vec = X.std(axis=0)
    X_scaled = (X-mean_vec)/(std_vec)
    return(X_scaled)


def calculate_eigen_matrix(X,n):
    
    cov_mat = np.cov(X.T)
    evals, evecs = np.linalg.eig(cov_mat)
    evecs = evecs.T
    
    sorted_indices = np.argsort(evals)
    sorted_indices = sorted_indices[::-1]
    sorted_evals = evals[sorted_indices] 
    sorted_evecs = evecs[:,sorted_indices]
    first_n = sorted_evecs[:,0:n]
    
    return first_n


def subset_selection(train_input, train_target, dev_input, dev_target, test_input, selected_features):
    train_scaled = std_scale(train_input)
    eigen_matrix = calculate_eigen_matrix(train_scaled, selected_features)

    train_input = train_input@eigen_matrix
    dev_input = dev_input@eigen_matrix
    test_input = test_input@eigen_matrix

    return train_input, train_target, dev_input, dev_target, test_input


# Define Activation Function for ReLU
def ReLU(z):
    return np.maximum(0,z)

# Derivative of ReLU
def derv_ReLU(z):
    res = (z > 0).astype(float)
    return res

# Define Activation Function for Sigmoid
def Sigmoid(z):
    return 1/(1 + np.exp(-z))

#Derivative of Sigmoid
def derv_Sigmoid(z):
    return Sigmoid(z)*(1-Sigmoid(z))

# Early Stopping criteria
def early_stopping(old_err, curr_err):
    if(old_err < curr_err):
        print("Early Stopping")
        return True
    else:
        return False
    
# Batch Normalization
def batch_normalize(x):
    mean_vec = x.mean(axis=0)
    std_vec = x.std(axis=0)
    mean_vec = mean_vec.reshape(1,mean_vec.shape[0])
    std_vec = std_vec.reshape(1,std_vec.shape[0])
    return (x - mean_vec)/std_vec

def min_max_scaleX01(data): 
    return (data - data.min(axis=0))/(data.max(axis=0) - data.min(axis=0))

def min_max_scaleX11(data): 
    return 2*((data - data.min(axis=0))/(data.max(axis=0) - data.min(axis=0))) - 1


def min_max_scaling(train_input, train_target, dev_input, dev_target, test_input):
    train_input = min_max_scaleX01(train_input)
    train_target = (train_target-1)/3
    dev_input = min_max_scaleX01(dev_input)
    dev_target = (dev_target-1)/3
    test_input = min_max_scaleX01(test_input)
    return train_input, train_target, dev_input, dev_target, test_input

#Order :  "New":1,"Recent":2,"Old":3,"Very Old":4
def convert_predictions(x):
    x = x*3+1
    result = []
    for i in x:
        if(i<1.5):
            result.append('New')
        elif(i<2.5):
            result.append('Recent')
        elif(i<3.5):
            result.append('Old')
        else:
            result.append('Very Old')
    return result

def store_results(result):
    df = pd.DataFrame(result, columns = ['Predictions'])
    df['Id'] = df.index+1
    df = df[['Id', 'Predictions']]
    df.to_csv('./22M2119.csv',index=False)


def get_test_data_predictions(net, inputs):
    '''
    Perform forward pass on test data and get the final predictions that can
    be submitted on Kaggle.
    Write the final predictions to the part2.csv file.
    Parameters
    ----------
        net : trained neural network
        inputs : test input, numpy array of shape m x d
    Returns
    ----------
        predictions (optional): Predictions obtained from forward pass
                                on test data, numpy array of shape m x 1
    '''
    old_wts = np.copy(net.weights)
    old_biases = np.copy(net.biases)
    res = net(inputs)
    net.weights = old_wts
    net.biases = old_biases
    
    return res

def read_data():
    '''
    Read the train, dev, and test datasets
    '''
    # TRAIN DATA and LABELS
    train = pd.read_csv("./data/train.csv")

    dic = {
        "New":1,
        "Recent":2,
        "Old":3,
        "Very Old":4
    }

    train['1'] = train['1'].apply(lambda x : dic[x])
    train_input = (train.iloc[:, 1:]).to_numpy()
    train_target = (train.iloc[:, 0]).to_numpy()
    train_target = train_target.reshape(train_target.shape[0], 1) # to make it vector
    
    # DEV DATA and LABELS
    dev = pd.read_csv("./data/dev.csv")
    dev['1'] = dev['1'].apply(lambda x : dic[x])
    dev_input = (dev.iloc[:, 1:]).to_numpy()
    dev_target = (dev.iloc[:, 0]).to_numpy()
    dev_target = dev_target.reshape(dev_target.shape[0], 1) # to make it vector

    
    #TEST DATA
    test_input = pd.read_csv("./data/test.csv").to_numpy()

    return train_input, train_target, dev_input, dev_target, test_input




class Net(object):
    '''
    '''
    def __init__(self, num_layers, num_units, selected_features):
        '''
        Initialize the neural network.
        Create weights and biases.
        Here, we have provided an example structure for the weights and biases.
        It is a list of weight and bias matrices, in which, the
        dimensions of weights and biases are (assuming 1 input layer, 2 hidden layers, and 1 output layer):
        weights: [(NUM_FEATS, num_units), (num_units, num_units), (num_units, num_units), (num_units, 1)]
        biases: [(num_units, 1), (num_units, 1), (num_units, 1), (num_units, 1)]
        Please note that this is just an example.
        You are free to modify or entirely ignore this initialization as per your need.
        Also you can add more state-tracking variables that might be useful to compute
        the gradients efficiently.
        Parameters
        ----------
            num_layers : Number of HIDDEN layers.
            num_units : Number of units in each Hidden layer.
        '''
        self.num_layers = num_layers
        self.num_units = num_units

        self.biases = []
        self.weights = []
        for i in range(num_layers):

            if i==0:
                # Input layer
                self.weights.append(np.random.uniform(-1, 1, size=(selected_features, self.num_units)))
            else:
                # Hidden layer
                self.weights.append(np.random.uniform(-1, 1, size=(self.num_units, self.num_units)))

            self.biases.append(np.random.uniform(-1, 1, size=(self.num_units, 1)))

        # Output layer
        self.biases.append(np.random.uniform(-1, 1, size=(1, 1)))
        self.weights.append(np.random.uniform(-1, 1, size=(self.num_units, 1)))

    def __call__(self, X):
        '''
        Forward propagate the input X through the network,
        and return the output.
        Note that for a classification task, the output layer should
        be a softmax layer. So perform the computations accordingly
        Parameters
        ----------
            X : Input to the network, numpy array of shape m x d
        Returns
        ----------
            y : Output of the network, numpy array of shape m x 1
        '''
        self.Z=[]
        self.A=[]   
        
        z_temp = X@self.weights[0] + (self.biases[0]).T
        z_temp = batch_normalize(z_temp)
    
        self.Z.append(z_temp)
        self.A.append(ReLU(self.Z[0]))
        
        for i in range(1,self.num_layers):
            z_temp = self.A[i-1]@self.weights[i] + (self.biases[i]).T
            z_temp = batch_normalize(z_temp)
            self.Z.append(z_temp)
            self.A.append(ReLU(self.Z[i]))
        
           
        z_temp = self.A[self.num_layers-1]@self.weights[self.num_layers] + (self.biases[self.num_layers]).T
        # z_temp = batch_normalize(z_temp)
        self.Z.append(z_temp)
        
        self.y_pred = self.Z[self.num_layers]
        return self.y_pred

    def backward(self, X, y, lamda):
        '''
        Compute and return gradients loss with respect to weights and biases.
        (dL/dW and dL/db)
        Parameters
        ----------
            X : Input to the network, numpy array of shape m x d
            y : Output of the network, numpy array of shape m x 1
            lamda : Regularization parameter.
        Returns
        ----------
            del_W : derivative of loss w.r.t. all weight values (a list of matrices).
            del_b : derivative of loss w.r.t. all bias values (a list of vectors).
        Hint: You need to do a forward pass before performing backward pass.
        '''
        Y = self.y_pred

        dz = []
        dA = []
        del_W = []
        del_b = []
        m = len(y)

        dz.insert(0, -(1/m)*(y-Y))
        del_W.insert(0, np.matmul(self.A[self.num_layers-1].T,dz[0]) + lamda*self.weights[self.num_layers])
        del_b.insert(0, np.matmul(np.ones((m,1)).T,dz[0]) + lamda*self.biases[self.num_layers])
        dA.insert(0, np.matmul(dz[0],self.weights[self.num_layers].T))


        # Wt optimization for wlast yet to be written
        for i in range(self.num_layers-1, 0, -1) :

            dz.insert(0, np.multiply(dA[0],derv_ReLU(self.Z[i])))
            del_W.insert(0, np.matmul(self.A[i-1].T,dz[0]) + lamda*self.weights[i])
            
            db_cl = dz[0].sum(axis=0)
            del_b.insert(0, db_cl.reshape(db_cl.shape[0],1) + lamda*self.biases[i])
            dA.insert(0, np.matmul(dz[0],self.weights[i].T))


        dz.insert(0, np.multiply(dA[0], derv_ReLU(self.Z[0])))
        db_cl = dz[0].sum(axis=0)
        del_b.insert(0, db_cl.reshape(db_cl.shape[0],1) + lamda*self.biases[0])
        del_W.insert(0, np.matmul(X.T, dz[0]) + lamda*self.weights[0])

        return del_W, del_b


class Optimizer(object):
    '''
    '''

    def __init__(self, learning_rate, optimizer):
        '''
        Create a Gradient Descent based optimizer with given
        learning rate.
        Other parameters can also be passed to create different types of
        optimizers.
        Hint: You can use the class members to track various states of the
        optimizer.
        '''
        self.learning_rate = learning_rate
        self.optimizer = optimizer
            

    def step(self, weights, biases, delta_weights, delta_biases):
        '''
        Parameters
        ----------
            weights: Current weights of the network.
            biases: Current biases of the network.
            delta_weights: Gradients of weights with respect to loss.
            delta_biases: Gradients of biases with respect to loss.
        '''
        if(self.optimizer == "gradient"):
            return self.gradient(weights, biases, delta_weights, delta_biases)
        elif(self.optimizer == "adam"):
            return self.adam(weights, biases, delta_weights, delta_biases)
        elif(self.optimizer == "rmsprop"):
            return self.rmsprop(weights, biases, delta_weights, delta_biases)
        elif(self.optimizer == "momentum"):
            return self.momentum(weights, biases, delta_weights, delta_biases)
        
        
        
    
    def gradient(self, weights, biases, delta_weights, delta_biases):
        for i in range(len(weights)):
            weights[i] = weights[i] - self.learning_rate*delta_weights[i]
            biases[i] = biases[i] - self.learning_rate*delta_biases[i]
        return weights, biases

def cross_entropy_loss(y, y_hat):
    '''
    Compute cross entropy loss
    Parameters
    ----------
        y : targets, numpy array of shape m x 1
        y_hat : predictions, numpy array of shape m x 1
    Returns
    ----------
        cross entropy loss
    '''
    return -1* np.sum(y*np.log(softmax(y_hat)))

def loss(y, y_hat):
    '''
    Compute Mean Squared Error (MSE) loss betwee ground-truth and predicted values.
    Parameters
    ----------
        y : targets, numpy array of shape m x 1
        y_hat : predictions, numpy array of shape m x 1
    Returns
    ----------
        MSE loss between y and y_hat.
    '''
    return np.mean((y-y_hat)**2)

def loss_regularization(weights, biases):
    '''
    Compute l2 regularization loss.
    Parameters
    ----------
        weights and biases of the network.
    Returns
    ----------
        l2 regularization loss 
    '''
    total = 0.0
    for wt in (weights):
        total += np.sum(wt**2)

    for bs in (biases):
        total += np.sum(bs**2)

    return total

def loss_fn(y, y_hat, weights, biases, lamda):
    '''
    Compute loss =  loss(..) + lamda * loss_regularization(..)
    Parameters
    ----------
        y : targets, numpy array of shape m x 1
        y_hat : predictions, numpy array of shape m x 1
        weights and biases of the network
        lamda: Regularization parameter
    Returns
    ----------
        l2 regularization loss 
    '''
    return loss(y, y_hat) + lamda * loss_regularization(weights, biases)

def get_loss(y, y_hat):
    '''
    Compute Root Mean Squared Error (RMSE) loss betwee ground-truth and predicted values.
    Parameters
    ----------
        y : targets, numpy array of shape m x 1
        y_hat : predictions, numpy array of shape m x 1
    Returns
    ----------
        RMSE between y and y_hat.
    '''
    return np.sqrt(loss(y,y_hat))




def train(
    net, optimizer, lamda, batch_size, max_epochs,
    train_input, train_target,
    dev_input, dev_target
):
    '''
    In this function, you will perform following steps:
        1. Run gradient descent algorithm for `max_epochs` epochs.
        2. For each bach of the training data
            1.1 Compute gradients
            1.2 Update weights and biases using step() of optimizer.
        3. Compute RMSE on dev data after running `max_epochs` epochs.
    Here we have added the code to loop over batches and perform backward pass
    for each batch in the loop.
    For this code also, you are free to heavily modify it.
    '''

    m = train_input.shape[0]
    old_err = float('inf')
    EARLY_STOPPING = False
    old_err = 99999999999999

    for e in range(max_epochs):
        
        epoch_loss = 0.
        for i in range(0, m, batch_size):
            batch_input = train_input[i:i+batch_size]
            batch_target = train_target[i:i+batch_size]
            
            
            # BATCH NORMALIZATION
            batch_input = batch_normalize(batch_input)

            #batch_target = (batch_target - np.mean(batch_target))/np.std(batch_target)
            # batch_target = (batch_target-np.min(batch_target))/(np.max(batch_target)-np.min(batch_target))
            
            pred = net(batch_input)

            # Compute gradients of loss w.r.t. weights and biases
            dW, db = net.backward(batch_input, batch_target, lamda)

            # Get updated weights based on current weights and gradients and update them
            net.weights, net.biases = optimizer.step(net.weights, net.biases, dW, db)
    

            # Compute loss for the batch
            batch_loss = loss_fn(batch_target, pred, net.weights, net.biases, lamda)
            epoch_loss += batch_loss

            #print(e, i, rmse(batch_target, pred), batch_loss)

            if(early_stopping(old_err, batch_loss)):
                EARLY_STOPPING = True
                break
        
        
        if(e%100==0):
            print(f"Main hoon epoch : {e} ::== Loss: ", epoch_loss)

        if(EARLY_STOPPING):
            break
        
    # After running `max_epochs` (for Part 1) epochs OR early stopping (for Part 2), compute the RMSE on dev data.
    dev_pred = net(dev_input)*3+1
    dev_target = dev_target*3+1
    loss = get_loss(dev_target, dev_pred)

    print('Loss on dev data: {:.5f}'.format(loss))

# Hyper-parameters 
max_epochs = 2000
batch_size = 64
learning_rate = 0.01
num_layers = 2
num_units = 64
lamda = 0.01 # Regularization Parameter
selected_features = NUM_FEATS

train_input, train_target, dev_input, dev_target, test_input = read_data()
train_input, train_target, dev_input, dev_target, test_input = min_max_scaling(train_input, train_target, dev_input, dev_target, test_input)

if(FEATURE_SELECTION == True):
    selected_features = 55
    train_input, train_target, dev_input, dev_target, test_input = subset_selection(train_input, train_target, dev_input, dev_target, test_input, selected_features)


net = Net(num_layers, num_units, selected_features)
optimizer = Optimizer(learning_rate, "gradient")
train(
    net, optimizer, lamda, batch_size, max_epochs,
    train_input, train_target,
    dev_input, dev_target
)
result = convert_predictions(get_test_data_predictions(net, test_input))
print(result)
store_results(result)

