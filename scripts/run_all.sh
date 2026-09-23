cd "$(dirname "$0")/.."
set -e
set -x
python3 -m pip install -r backend/requirements.txt
python3 -m pip install matplotlib networkx flake8
python3 -m ml.inference.route_optimizer
python3 -m ml.training.seaice_train
python3 -m ml.training.seaice_train_convlstm
python3 -m ml.training.trajectory_train
python3 -m ml.training.trajectory_train_lstm

python3 -c "
from ml.inference.seaice_predict import predict_concentration
from ml.inference.trajectory_predict import project_trajectory
pred = predict_concentration(0.4, 0.42, 0.38, 150, -65.0, -60.0)
assert 0.0 <= pred <= 1.0, f'sea-ice prediction out of range: {pred}'
path = project_trajectory(-65.0, -58.0, 0.01, -0.005, 0.005, 0.002, num_steps=3)
assert len(path) == 4, f'expected 4 points (start + 3 steps), got {len(path)}'
print('Inference sanity checks passed')
"

python3 -m mlops.ci_checks
python3 -m mlops.monitor
