#%% imports
import sys
sys.path.append("..")   # fix to import modules from root
from src.general_imports import *

from src import modelling_bio_beta as modelling_bio
import arviz as az

from sklearn.linear_model import LinearRegression

amdata = ad.read_h5ad('../exports/wave3_meta.h5ad', backed='r')
# amdata_bio = ad.read_h5ad('../exports/wave3_acc.h5ad')

horvath_coef = pd.read_csv('../resources/Horvath_coef.csv', index_col=0)
intersection = amdata.obs.index.intersection(horvath_coef.index)
amdata_horvath = amdata[intersection].to_memory()

horvath_data = pd.read_csv('../exports/GS-P2-Wave3-Phe_hyperHypo.csv', index_col=0)
horvath_data.columns[150:200]
age = horvath_data['age'].values
horvath_data = horvath_data.iloc[:,3:]
ages = np.broadcast_to(age, (horvath_data.shape[1], horvath_data.shape[0])).T
horvath_data = horvath_data - ages

# %%
clocks = ['Horvath', 'Hannum']
# clocks = ['Hannum','SkinClock','Horvath']
offsets=[0.01,0.02,0.03,0.04,0.05,0.15]
offsets=[0.02,0.05]
all_offsets = sorted([-offset for offset in offsets]) + [0] + offsets

all_clock_data = pd.DataFrame()
for clock in clocks:
    columns =   [f'{int(offset*100)}%MinusAbs-{clock}' for offset in sorted(offsets, reverse=True)] + \
            [clock] + \
            [f'{int(offset*100)}%PlusAbs-{clock}' for offset in offsets] 
    clock_data = horvath_data[columns].copy()
    clock_data.columns = all_offsets
    clock_data['clock'] = clock
    all_clock_data = pd.concat([all_clock_data, clock_data])

# all_clock_data['shift'] = all_clock_data.groupby('clock')[0].transform('mean')
# all_clock_data[all_offsets] = all_clock_data[all_offsets].values - np.broadcast_to(all_clock_data['shift'], 
#                                                        ( len(all_offsets), all_clock_data.shape[0])).T

shifts = all_clock_data.groupby('clock')[0].transform('mean')
all_clock_data[all_offsets] = all_clock_data[all_offsets].values - np.broadcast_to(shifts, 
                                                       ( len(all_offsets), all_clock_data.shape[0])).T


df = all_clock_data.melt(id_vars='clock', var_name='offset', value_name='age acceleration')
# sns.boxplot(data=df, x='clock', y='age acceleration', hue='offset',  showfliers=False)
# %%
ax = plot.row(figsize=(9.5, 6))
plot.fonts(8)

ax.axhline(y=0, dashes=[5,3], color='tab:grey')
sns.boxplot(data=df, x='offset', y='age acceleration', hue='clock',  showfliers=False, ax=ax)
sns.despine()

ax.set_ylabel('Clock acceleration')
ax.set_xlabel('Applied global bias')
ax.get_figure().tight_layout()

# %% saving
ax.get_figure().savefig(f'{paths.FIGURES_DIR}/fig1/1G_global_bias_problem.svg')
ax.get_figure().savefig(f'{paths.FIGURES_DIR}/fig1/1G_global_bias_problem.png')

# %%

accs =[]

for offset in tqdm(all_offsets):
    amdata_bio_offset = amdata_bio.copy()
    amdata_bio_offset.X = amdata_bio.X+offset
    maps = modelling_bio.person_model(amdata_bio_offset, return_trace=False, return_MAP=True, show_progress=False, cores=4)['map']
    accs.append(maps['acc'])

accs = pd.DataFrame(accs, index=np.round(all_offsets,2)).T
accs.mean(axis=0)
shifts = np.broadcast_to(accs.mean(axis=0), (accs.shape[0], len(all_offsets)))
shifts.shape
pd.DataFrame(accs - shifts, columns=np.round(all_offsets,2)).T[0].hist(bins=50)
pd.DataFrame(accs  , index=np.round(all_offsets,2)).T.hist(bins=50)
(accs-shifts).hist(bins=50)
accs.mean()
accss=accs
accs=accss
accs = accs-shifts


accs_df=accs.melt(var_name='offset', value_name='acc').assign(type='acc')
# %%
horvaths_df = all_clock_data[all_clock_data.clock=='Horvath'].copy()
horvaths_df=horvaths_df[all_offsets].melt(var_name='offset', value_name='acc').assign(type='horvath')
accs_df['std'] = accs_df.groupby('offset')['acc'].transform('std')
accs_df['normalised_acc'] = accs_df.acc/accs_df['std']
horvaths_df['std'] = horvaths_df.groupby('offset')['acc'].transform('std')
horvaths_df['normalised_acc'] = horvaths_df.acc/horvaths_df['std']

df = pd.concat((accs_df, horvaths_df), axis=0)
df = df[['type','offset','normalised_acc']]
df.loc[df.type=='acc', 'type'] = 'Acceleration'
df.loc[df.type=='horvath', 'type'] = 'Horvath (2013)'
# %% plot

plt.rc('font', size=8) 
ax = plot.row('', figsize=(3.6,2.6))
sns.despine()

ax=sns.boxplot(data=df, x='offset', 
                y='normalised_acc', hue='type', showfliers=False)
ax.axhline(y=0, dashes=[5,3], color='tab:grey')

ax.set_xlabel('Offset')
ax.set_ylabel('Normalised acceleration')
ax.legend(title='Clock')

