## Keyring の設定方法

```
$ keyring set Bitflyer Bitflyer_id
>> input password: 保存したいパスワードを保存
$ keyring set Bitflyer 上記のシークレットキー
```

ここの方法に従って，セットアップする
https://keyring.readthedocs.io/en/latest/

### Ubuntuでのセットアップ

```
$ pip install SecretStorage
$ pip install dbus-python
```
これらがうまく導入できなければ，直接ダウンロードしてきて，pip install

## VScodeでのPytestの実装方法

コマンドパレットより
`Python: Configure tests `
で自動入力される
