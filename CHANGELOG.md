## v3.7.1 (2026-11-15)

### Feat

- drop python 3.9, add 3.15, and guard empty cli argv (#267)

## [4.1.0](https://github.com/zifeo/dataconf/compare/dataconf-v4.0.0...dataconf-v4.1.0) (2026-11-15)


### Features

* drop python 3.10 and pin patched filelock in the lockfile ([#278](https://github.com/zifeo/dataconf/issues/278)) ([6a37202](https://github.com/zifeo/dataconf/commit/6a37202d5982a0ed4cab79450dd069c3320c0c47))

## [4.0.0](https://github.com/zifeo/dataconf/compare/dataconf-v3.7.1...dataconf-v4.0.0) (2026-11-15)


### ⚠ BREAKING CHANGES

* update pyparsing and pyhocon ([#145](https://github.com/zifeo/dataconf/issues/145))
* add cli source and rename env dict/list to env vars ([#48](https://github.com/zifeo/dataconf/issues/48))

### Features

* add cli source and rename env dict/list to env vars ([#48](https://github.com/zifeo/dataconf/issues/48)) ([a56a513](https://github.com/zifeo/dataconf/commit/a56a5135c834199eb15478a30d6f8886d0a1993f))
* add ignore_unexpected option to ignore unwanted keys ([7c2c637](https://github.com/zifeo/dataconf/commit/7c2c637add405f66e03a121109696d02fd5e8eae))
* add literal support ([#119](https://github.com/zifeo/dataconf/issues/119)) ([5ee8c67](https://github.com/zifeo/dataconf/commit/5ee8c67fa1b62a50098ca72186c0985ddfdd0d65))
* add support for `pathlib.Path` type ([#126](https://github.com/zifeo/dataconf/issues/126)) ([74810c0](https://github.com/zifeo/dataconf/commit/74810c0d8ac513863762ac9b07893ba0a58b09a1))
* add support for any ([5074796](https://github.com/zifeo/dataconf/commit/5074796acae4778492ebed9d169f46e6c89a0dd7))
* add support for disambiguating subtypes  ([#45](https://github.com/zifeo/dataconf/issues/45)) ([3997e56](https://github.com/zifeo/dataconf/commit/3997e56a511ba782897e68d0b6726e8b5263a8f1))
* add support for tuples ([#152](https://github.com/zifeo/dataconf/issues/152)) ([1a5c567](https://github.com/zifeo/dataconf/commit/1a5c5677585e012cf04a51922aff64af6b51cd8a))
* add support fro string enum ([#88](https://github.com/zifeo/dataconf/issues/88)) ([970beff](https://github.com/zifeo/dataconf/commit/970befff1add15f5450272d86f7bdb89f43bd0fe))
* add timedelta support ([#134](https://github.com/zifeo/dataconf/issues/134)) ([fec2d16](https://github.com/zifeo/dataconf/commit/fec2d16e358aa178833a077a146acb3175a69fa9))
* add TOML load and dump ([#270](https://github.com/zifeo/dataconf/issues/270)) ([8b58237](https://github.com/zifeo/dataconf/commit/8b58237ca2ecc2e73df4dd3ef3d82658dda54fd0))
* add yaml source support ([#51](https://github.com/zifeo/dataconf/issues/51)) ([b3a0cb8](https://github.com/zifeo/dataconf/commit/b3a0cb805f0624d4649a87d847336b91fc32dc4b))
* commitizen ([4840c65](https://github.com/zifeo/dataconf/commit/4840c655ad130ac596d165c703c9032fc1c3523e))
* dependabot ([#69](https://github.com/zifeo/dataconf/issues/69)) ([256712d](https://github.com/zifeo/dataconf/commit/256712d706dda771e0c025e2acd154922ac13287))
* deps update and support for prefixless env parsing ([8109cc4](https://github.com/zifeo/dataconf/commit/8109cc40f2f4cd08c3fc2bb3a55dcc1971b90a30))
* drop python 3.9 and env list fixes ([#177](https://github.com/zifeo/dataconf/issues/177)) ([b1d5980](https://github.com/zifeo/dataconf/commit/b1d5980420d589f2c28ad4973016fbda8fb820b5))
* drop python 3.9, add 3.15, and guard empty cli argv ([#267](https://github.com/zifeo/dataconf/issues/267)) ([7d53096](https://github.com/zifeo/dataconf/commit/7d530960e6b6d3eac97f39539f1376905a5c2ff4))
* implicit default, close [#222](https://github.com/zifeo/dataconf/issues/222) ([#224](https://github.com/zifeo/dataconf/issues/224)) ([b0110f1](https://github.com/zifeo/dataconf/commit/b0110f139f8c7ec206df2fb69dcc5521c29bb797))
* migrate to uv and harden remaining parse edge cases ([#273](https://github.com/zifeo/dataconf/issues/273)) ([952cbfe](https://github.com/zifeo/dataconf/commit/952cbfef7e435513af280e370d4409f4de3cc10b))
* optional file loading and upgrades ([#207](https://github.com/zifeo/dataconf/issues/207)) ([e9c4249](https://github.com/zifeo/dataconf/commit/e9c4249d806495d3506894ab645fb8ab9bae9504))
* support for basic Enum/IntEnum implementation ([#44](https://github.com/zifeo/dataconf/issues/44)) ([fa32127](https://github.com/zifeo/dataconf/commit/fa3212711ff3e0737ef905ec56be389ab4d83a8e))
* support StrEnum from python 3.11 ([#91](https://github.com/zifeo/dataconf/issues/91)) ([41f1320](https://github.com/zifeo/dataconf/commit/41f13204e71428d038367221fa50e096a9c769d7))
* update pre-commit ([9e13da4](https://github.com/zifeo/dataconf/commit/9e13da4a811bf671a6016b09ab10d19c4be62cd7))
* upgrade deps and switch to ruff ([#68](https://github.com/zifeo/dataconf/issues/68)) ([33aefa9](https://github.com/zifeo/dataconf/commit/33aefa9df2484937bb1fd804fb4a86b9f1260538))


### Bug Fixes

* 19 ([db577f0](https://github.com/zifeo/dataconf/commit/db577f0b22dd058290e61d65267efc2909cb2c2e))
* 20 ([da7addc](https://github.com/zifeo/dataconf/commit/da7addca7ace596ce09a7ca48d6f896aecd621fd))
* 27 ([#29](https://github.com/zifeo/dataconf/issues/29)) ([dbc8d73](https://github.com/zifeo/dataconf/commit/dbc8d7335b11a458c61500c3bb57ca9e42f26b80))
* dumps close [#54](https://github.com/zifeo/dataconf/issues/54) ([#55](https://github.com/zifeo/dataconf/issues/55)) ([368dfce](https://github.com/zifeo/dataconf/commit/368dfcecca5664d2991bdbca0c9f39813ebef062))
* fix failing tests ([#128](https://github.com/zifeo/dataconf/issues/128)) ([d6e2e3b](https://github.com/zifeo/dataconf/commit/d6e2e3be1e43b3e498d0384f3ddf4578dcf62dcb))
* for issue with nested dataclasses that have default values [#98](https://github.com/zifeo/dataconf/issues/98) ([97c3727](https://github.com/zifeo/dataconf/commit/97c3727585e44d9020d516427880928ff92f087f))
* harden loaders, unions, env lists, and dumps ([#271](https://github.com/zifeo/dataconf/issues/271)) ([3ab3909](https://github.com/zifeo/dataconf/commit/3ab3909ef22ee1fce139f4b93467daa057de0a0f))
* license ([9771bcc](https://github.com/zifeo/dataconf/commit/9771bcc8212accb4a84e2ea8f82c41f54fdceaca))
* list must start with 0 ([5ea7c7a](https://github.com/zifeo/dataconf/commit/5ea7c7a60b227c12e3668b97b27e40c6432980c7))
* parse env bools without bool(str) ([#254](https://github.com/zifeo/dataconf/issues/254)) ([c202431](https://github.com/zifeo/dataconf/commit/c20243137324d6bb1adc0de3fda2c7f11d6a2134))
* readme ([7ba2fcf](https://github.com/zifeo/dataconf/commit/7ba2fcfe3afcb091cfa7361a8ae3abd3452a07e0))
* remote loading error, close [#57](https://github.com/zifeo/dataconf/issues/57) ([d3a82bc](https://github.com/zifeo/dataconf/commit/d3a82bc7e94caef99b50f9dc4ab965b89b561609))
* resolve postponed annotations with get_type_hints ([#269](https://github.com/zifeo/dataconf/issues/269)) ([9e70bde](https://github.com/zifeo/dataconf/commit/9e70bdedc7469bbd67055b1547619c6e9caa3a30))
* typing for dict, close [#64](https://github.com/zifeo/dataconf/issues/64) ([#65](https://github.com/zifeo/dataconf/issues/65)) ([172f895](https://github.com/zifeo/dataconf/commit/172f89554d78b38edcc6f6ceff95d40b028dbf68))
* union alternative syntax [#112](https://github.com/zifeo/dataconf/issues/112) ([#113](https://github.com/zifeo/dataconf/issues/113)) ([cf1f944](https://github.com/zifeo/dataconf/commit/cf1f9444146aa71f7c0e97916860916567c13143))
* union and yaml loader fixes ([#92](https://github.com/zifeo/dataconf/issues/92)) ([ff76e04](https://github.com/zifeo/dataconf/commit/ff76e049c1af5886b5f47d130858ef0d853b6c9b))


### Miscellaneous Chores

* update pyparsing and pyhocon ([#145](https://github.com/zifeo/dataconf/issues/145)) ([e28e1bf](https://github.com/zifeo/dataconf/commit/e28e1bf5cfe73ecb6aa918da46c494af95dac44f))

## v3.7.0 (2026-08-20)

### Fix

- parse env bools without bool(str) (#254)

## v3.6.0 (2025-08-01)

### Feat

- implicit default, close #222 (#224)

## v3.5.0 (2025-07-23)

### Fix

- Issue 219 nested dataclasses (#220)

## v3.4.0 (2025-03-23)

### Feat

- optional file loading and upgrades (#207)

## v3.3.0 (2024-09-16)

### Feat

- drop python 3.9 and env list fixes (#177)

## v3.2.0 (2024-05-31)

## v3.1.0 (2024-04-02)

### Feat

- add support for tuples (#152)

## v3.0.0 (2024-03-08)


- update pyparsing and pyhocon (#145)

## v2.5.0 (2024-02-01)

### Feat

- add timedelta support (#134)

## v2.4.0 (2024-01-01)

### Feat

- update pre-commit
- add support for `pathlib.Path` type (#126)

### Fix

- fix failing tests (#128)

## v2.3.0 (2023-10-31)

### Feat

- add literal support (#119)

## v2.2.2 (2023-09-24)

### Fix

- union alternative syntax #112 (#113)

## v2.2.1 (2023-05-26)

### Fix

- for issue with nested dataclasses that have default values #98

## v2.2.0 (2023-05-23)

### Feat

- support StrEnum from python 3.11 (#91)
- add support fro string enum (#88)
- dependabot (#69)
- upgrade deps and switch to ruff (#68)

### Fix

- union and yaml loader fixes (#92)
- license

## v2.1.3 (2022-12-05)

### Fix

- typing for dict, close #64 (#65)

## v2.1.2 (2022-10-22)

### Fix

- readme
- remote loading error, close #57

## v2.1.1 (2022-09-16)

### Fix

- dumps close #54 (#55)

## v2.1.0 (2022-07-31)

### Feat

- add yaml source support (#51)

## v2.0.0 (2022-06-28)

### Feat

- add support for any
- add cli source and rename env dict/list to env vars (#48)
- add support for disambiguating subtypes  (#45)
- support for basic Enum/IntEnum implementation (#44)

## v1.5.0 (2022-04-29)

### Feat

- add ignore_unexpected option to ignore unwanted keys
- deps update and support for prefixless env parsing
- commitizen

### Fix

- list must start with 0

## v1.4.0 (2022-03-08)

### Feat

- commitizen

## v1.3.0 (2022-02-09)

## v1.2.0 (2021-11-07)

## v1.1.0 (2021-11-07)

## v1.0.3 (2021-11-04)

## v1.0.2 (2021-10-29)

## v1.0.1 (2021-10-28)

## v1.0.0 (2021-10-28)

## v0.4.0 (2021-10-28)

## v0.3.0 (2021-10-17)

## v0.2.1 (2021-10-13)

## v0.2.0 (2021-10-08)

## v0.1.6 (2021-09-20)

## v0.1.5 (2021-08-23)

## v0.1.3 (2021-05-06)

## v0.1.2 (2021-01-31)

## v0.1.1 (2021-01-31)
