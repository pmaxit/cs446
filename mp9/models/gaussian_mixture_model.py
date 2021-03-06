"""Implements the Gaussian Mixture model, and trains using EM algorithm."""
import numpy as np
import scipy
from scipy.stats import multivariate_normal
from scipy.cluster.vq import kmeans2


class GaussianMixtureModel(object):
    """Gaussian Mixture Model."""

    def __init__(self, n_dims, n_components=1, max_iter=10, reg_covar=1e-6):
        """
        Gaussian Mixture Model init funtion.

        Args:
            n_dims: The dimension of the feature.
            n_components: Number of Gaussians in the GMM.
            max_iter: Number of steps to run EM.
            reg_covar: Amount to regularize the covariance matrix, (i.e. add to the diagonal of covariance matrices).
        """
        self._n_dims = n_dims
        self._n_components = n_components
        self._max_iter = max_iter
        self._reg_covar = reg_covar

        self._mu = np.random.rand(self._n_components, self._n_dims)
        self._pi = np.random.uniform(size=(self._n_components, 1))
        self._sigma = np.repeat(100 * np.eye(self._n_dims)[np.newaxis, :, :], self._n_components, axis=0)

    def fit(self, x):
        """Run EM steps.

        Runs EM steps for max_iter number of steps.

        Args:
            x(numpy.ndarray): Feature array of dimension (N, ndims).
        """

        self._mu = x[np.random.choice(x.shape[0], size=self._n_components), :]

        for i in range(self._max_iter):
            print("iter:", i)
            self._m_step(x, self._e_step(x))

    def _e_step(self, x):
        """E step.

        Wraps around get_posterior.

        Args:
            x(numpy.ndarray): Feature array of dimension (N, ndims).
        Returns:
            z_ik(numpy.ndarray): Array containing the posterior probability of each example, dimension (N, n_components).
        """
        return self.get_posterior(x)

    def _m_step(self, x, z_ik):
        """M step, update the parameters.

        Args:
            x(numpy.ndarray): Feature array of dimension (N, ndims).
            z_ik(numpy.ndarray): Array containing the posterior probability of each example, dimension (N, n_components). (Alternate way of representing categorical distribution of z_i)
        """

        self._pi = np.sum(z_ik, axis=0) / x.shape[0]

        self._mu = np.dot(z_ik.T, x) / np.sum(z_ik, axis=0).reshape(-1, 1)

        _cov = np.zeros_like(self._sigma)
        _regularizer = np.zeros((x.shape[1], x.shape[1]))
        np.fill_diagonal(_regularizer, self._reg_covar)

        for k in range(self._n_components):
            _x_zero_center = x - self._mu[k, :]
            _cov[k, :, :] = np.dot(_x_zero_center.T, z_ik[:, k][:, np.newaxis] * _x_zero_center) / (np.sum(z_ik, axis=0)[k]) + _regularizer
        self._sigma = _cov

    def get_conditional(self, x):
        """Compute the conditional probability.

        p(x_i|z_i=k)

        Args:
            x(numpy.ndarray): Feature array of dimension (N, ndims).
        Returns:
            response(numpy.ndarray): The conditional probability for each example, dimension (N, n_components).
        """

        response = []
        for k in range(self._n_components):
            response.append(self._multivariate_gaussian(x, self._mu[k], self._sigma[k]))
        return np.array(response).T

    def get_marginals(self, x):
        """Compute the marginal probability.

        p(x^(i)|pi, mu, sigma)

        Args:
            x(numpy.ndarray): Feature array of dimension (N, ndims).
        Returns:
            The marginal probability for each example, dimension (N,).
        """
        return np.dot(self.get_conditional(x), self._pi).flatten()

    def get_posterior(self, x):
        """Compute the posterior probability.

        p(z_{ik}=1|x^(i))

        Args:
            x(numpy.ndarray): Feature array of dimension (N, ndims).
        Returns:
            z_ik(numpy.ndarray): Array containing the posterior probability of each example, dimension (N, n_components).
        """
        return ((self.get_conditional(x) * self._pi.T).T / (self.get_marginals(x) + np.finfo(float).eps)).T

    def _multivariate_gaussian(self, x, mu_k, sigma_k):
        """Multivariate Gaussian, implemented for you.

        Args:
            x(numpy.ndarray): Array containing the features of dimension (N, ndims)
            mu_k(numpy.ndarray): Array containing one single mean (ndims,)
            sigma_k(numpy.ndarray): Array containing one signle covariance matrix (ndims, ndims)
        """
        return multivariate_normal.pdf(x, mu_k, sigma_k)

    def supervised_fit(self, x, y):
        """Assign each cluster with a label through counting.

        For each cluster, find the most common digit using the provided (x, y)
        and store it in self.cluster_label_map.
        self.cluster_label_map should be a list of length n_components,
        where each element maps to the most common digit in that cluster.
        (e.g. If self.cluster_label_map[0] = 9. Then the most common digit
        in cluster 0 is 9.
        Args:
            x(numpy.ndarray): Array containing the feature of dimension (N, ndims).
            y(numpy.ndarray): Array containing the label of dimension (N,)
        """
        self.cluster_label_map = np.random.rand(self._n_components).tolist()

        _label = np.argmax(self.get_posterior(x), axis=1)

        for k in range(self._n_components):
            _i = np.where(_label == k)
            if _i[0].size:
                _chosen_label = scipy.stats.mode(y[_i])[0][0]
                self.cluster_label_map[k] = _chosen_label

    def supervised_predict(self, x):
        """Predict a label for each example in x.

        Find the get the cluster assignment for each x, then use
        self.cluster_label_map to map to the corresponding digit.
        Args:
            x(numpy.ndarray): Array containing the feature of dimension (N, ndims).
        Returns:
            y_hat(numpy.ndarray): Array containing the predicted label for each x, dimension (N,)
        """
        _label = np.argmax(self.get_posterior(x), axis=1)
        y_hat = [self.cluster_label_map[i] for i in _label]
        return np.array(y_hat)
