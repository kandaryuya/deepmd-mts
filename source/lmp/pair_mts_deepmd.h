// SPDX-License-Identifier: LGPL-3.0-or-later
#ifndef LAMMPS_VERSION_NUMBER
#error Please define LAMMPS_VERSION_NUMBER to yyyymmdd
#endif

#ifdef PAIR_CLASS

PairStyle(deepmd/mts,PairMtsDeepMD)

#else

#ifndef LMP_PAIR_MTS_NNP_H
#define LMP_PAIR_MTS_NNP_H

#include "pair.h"
#ifdef DP_USE_CXX_API
#ifdef LMPPLUGIN
#include "DeepPot.h"
#else
#include "deepmd/DeepPot.h"
#endif
namespace deepmd_compat = deepmd;
#else
#ifdef LMPPLUGIN
#include "deepmd.hpp"
#else
#include "deepmd/deepmd.hpp"
#endif
namespace deepmd_compat = deepmd::hpp;
#endif
#include <fstream>
#include <iostream>
#include <map>
#include "pair_deepmd.h"

#define FLOAT_PREC double

namespace LAMMPS_NS {

class PairMtsDeepMD : public PairDeepMD {
 public:
  PairMtsDeepMD(class LAMMPS *);
  ~PairMtsDeepMD() override;
  void compute(int, int) override;
  void *extract(const char *, int &) override;
  void settings(int, char **) override;
  void coeff(int, char **) override;
  void init_style() override;
  void write_restart(FILE *) override;
  void read_restart(FILE *) override;
  double init_one(int i, int j) override;
  void print_summary(const std::string pre) const;
  int get_node_rank();
  void extend(int &extend_inum,
              std::vector<int> &extend_ilist,
              std::vector<int> &extend_numneigh,
              std::vector<std::vector<int> > &extend_neigh,
              std::vector<int *> &extend_firstneigh,
              std::vector<double> &extend_coord,
              std::vector<int> &extend_atype,
              int &extend_nghost,
              std::map<int, int> &new_idx_map,
              std::map<int, int> &old_idx_map,
              const deepmd_compat::InputNlist &lmp_list,
              const std::vector<double> &coord,
              const std::vector<int> &atype,
              const int nghost,
              const std::vector<double> &spin,
              const int numb_types,
              const int numb_types_spin,
              const std::vector<double> &virtual_len);
  void cum_sum(std::map<int, int> &, std::map<int, int> &);

  std::string get_file_content(const std::string &model);
  std::vector<std::string> type_names;
  double ener_unit_cvt_factor, dist_unit_cvt_factor, force_unit_cvt_factor;

 protected:
  virtual void allocate();
  double **scale;

 private:
  deepmd_compat::DeepPot deep_pot;

  // 新しい変数の追加
  deepmd_compat::DeepPot deep_pot_4;        // カットオフ半径4Å用のDPモデル
  deepmd_compat::DeepPot deep_pot_6;        // カットオフ半径6Å用のDPモデル
  double cutoff_4;                          // 4Åモデルのカットオフ半径
  double cutoff_6;                          // 6Åモデルのカットオフ半径
  unsigned numb_models;
  double cutoff;
  int numb_types;
  int numb_types_spin;
  int timestep;
  int update_flag;
  int dim_fparam;
  int dim_aparam;
  std::vector<double> virtual_len;
  std::vector<double> spin_norm;
  int extend_inum;
  std::vector<int> extend_ilist;
  std::vector<int> extend_numneigh;
  std::vector<std::vector<int> > extend_neigh;
  std::vector<int *> extend_firstneigh;
  std::vector<double> extend_dcoord;
  std::vector<int> extend_dtype;
  int extend_nghost;
  // for spin systems, search new index of atoms by their old index
  std::map<int, int> new_idx_map;
  std::map<int, int> old_idx_map;
  std::vector<double> fparam;
  std::vector<double> aparam;

  void make_fparam_from_compute(std::vector<double> &fparam);
  bool do_compute_fparam;
  std::string compute_fparam_id;
  void make_aparam_from_compute(std::vector<double> &aparam);
  bool do_compute_aparam;
  std::string compute_aparam_id;

  void make_ttm_fparam(std::vector<double> &fparam);

  void make_ttm_aparam(std::vector<double> &dparam);
  bool do_ttm;
  std::string ttm_fix_id;
  std::vector<int> type_idx_map;
};

}  // namespace LAMMPS_NS

#endif
#endif
