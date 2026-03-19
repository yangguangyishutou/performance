import sys
import tiktoken

code = """f,ax=plt.subplots(2,2,figsize=(15,12))

# 1、模型
rf=RandomForestClassifier(n_estimators=500,random_state=0)
# 2、训练
rf.fit(X,Y)
# 3、重要性排序
pd.Series(rf.feature_importances_, X.columns).sort_values(ascending=True).plot.barh(width=0.8,ax=ax[0,0])
# 4、添加标题
ax[0,0].set_title('Feature Importance in Random Forests')

ada=AdaBoostClassifier(n_estimators=200,learning_rate=0.05,random_state=0)
ada.fit(X,Y)
pd.Series(ada.feature_importances_, X.columns).sort_values(ascending=True).plot.barh(width=0.8,ax=ax[0,1],color='#9dff11')
ax[0,1].set_title('Feature Importance in AdaBoost')

gbc=GradientBoostingClassifier(n_estimators=500,learning_rate=0.1,random_state=0)
gbc.fit(X,Y)
pd.Series(gbc.feature_importances_, X.columns).sort_values(ascending=True).plot.barh(width=0.8,ax=ax[1,0],cmap='RdYlGn_r')
ax[1,0].set_title('Feature Importance in Gradient Boosting')

xgbc=xg.XGBClassifier(n_estimators=900,learning_rate=0.1)
xgbc.fit(X,Y)
pd.Series(xgbc.feature_importances_, X.columns).sort_values(ascending=True).plot.barh(width=0.8,ax=ax[1,1],color='#FD0F00')
ax[1,1].set_title('Feature Importance in XgBoost')

plt.show()"""

enc = tiktoken.get_encoding("cl100k_base")
ids = enc.encode(code)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

print("=== 代码 ===")
print(code)

print("\n=== 切分方式（每个 token 及对应文本）===\n")
for i, tid in enumerate(ids, start=1):
    piece = enc.decode([tid])
    print(f"[{i}] id={tid:5d} piece={piece!r}")

print("\n=== Token 数量 ===")
print(len(ids))

