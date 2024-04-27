import os
import dotenv
import pandas as pd
import scipy.stats as sp
import seaborn as sns
import matplotlib.pyplot as plt

dotenv.load_dotenv()


df = pd.read_csv('./dataset/repos.csv')

df_filtered = df[(df['total_comments_pr'] < 11) & (df['total_pr'] < 3100) & (df['total_pr'] > 0)]

Q1 = df_filtered['total_pr'].quantile(0.25)
Q3 = df_filtered['total_pr'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

sns.scatterplot(x='total_pr', y='total_comments_pr', data=df_filtered)
plt.title('Total de comentários da PR x Feedback final da PR')
plt.xlabel('Feedback final da PR')
plt.ylabel('Total de comentários da PR')

plt.gca().get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))

r_spearman, p_spearman = sp.spearmanr(df_filtered['total_pr'], df_filtered['total_comments_pr'])

ax = plt.gca() 

plt.text(0.05, 0.8, "Correlação de Spearman = {:.2f}".format(r_spearman), transform=ax.transAxes, color='green')

plt.show()