import os
import dotenv
import pandas as pd
import scipy.stats as sp
import seaborn as sns
import matplotlib.pyplot as plt

dotenv.load_dotenv()


df = pd.read_csv('./dataset/repos.csv')

df_filtered = df[df['grand_total_rows_added_and_removed'] < 10000000]

Q1 = df_filtered['total_pr'].quantile(0.25)
Q3 = df_filtered['total_pr'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

sns.scatterplot(x='total_pr', y='grand_total_rows_added_and_removed', data=df_filtered)
plt.title('Tamanho do PR x Feedback Final das Revisões')
plt.xlabel('Feedback Final das Revisões')
plt.ylabel('Tamanho do PR')

plt.gca().get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))

r_spearman, p_spearman = sp.spearmanr(df_filtered['total_pr'], df_filtered['grand_total_rows_added_and_removed'])

ax = plt.gca() 

plt.text(0.05, 0.8, "Correlação de Spearman = {:.2f}".format(r_spearman), transform=ax.transAxes, color='green')

plt.show()