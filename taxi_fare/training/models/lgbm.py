import lightgbm as lgb

def create_lgbm_model(X_train, y_train, param, num_rounds):
    """
    Create a light gbm model
    """
    train_lgb_dataset = lgb.Dataset(X_train, label=y_train.values)
    return lgb.train(param, train_lgb_dataset, num_rounds)