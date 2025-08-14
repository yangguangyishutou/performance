class ModelInfo:
    """数据类，用于表示一个模型及其基本派生信息。"""
    def __init__(self, model_name: str, derive_type: str = None, father_model: str = None):
        self.model_name = model_name
        self.derive_type = derive_type
        self.father_model = father_model

    def __eq__(self, other):
        """自定义比较方法，模型名字一致即认为相等。"""
        if isinstance(other, ModelInfo):
            return self.model_name == other.model_name
        return False
        
    def __repr__(self):
        """提供一个更具信息量的字符串表示。"""
        return f"Model(name='{self.model_name}', type='{self.derive_type}', parent='{self.father_model}')"