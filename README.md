Neltharion
==========

## 耐萨里奥, 死亡之翼. 别问我为啥叫这个, 比「牛油」要好太多了吧.

## 这是干啥的

给前端纯静态项目编译上线用的.

## 这货的原理是啥

1. 项目里需要配置 `compile.sh`, 执行他来编译源文件生成静态文件.
2. 项目里需要配置 `rules`, 是一个 JSON 格式的文件, 写着哪些文件夹需要被 copy 到哪些目的地去. 例如

	```JSON
	{
    	"target1": "ems/topic",
    	"target2": "ems/test",
	}
	```
说明代码根目录下的 `target1` 文件夹里的内容会被全部 copy 到 `ems/topic/:sha` 这个文件夹里, `sha` 是这一次编译的 git hash 值. 同理 `target2` 里的全部内容会被 copy 到 `ems/test/:sha` 里.

3. 经过上面两步, 给项目配置好 gitlab webhook, 就可以在特定时候触发这边的编译行为. 编译完成后代码会 copy 去特定位置, 这样 nginx / openresty 只需要配置好自己的 serve root 就可以 serve 这个仓库了. 如果需要切换版本, 只需要把另外一个 git hash 值指定的目录里的所有文件 copy 到 nginx / openresty 配置的 serve root即可. 

	例如对应用 `ems/topic`, 里面现在有 `sha1`, `sha2`, `sha3` 这三个 git sha 值的目录, 里面是三个对应版本编译出来的静态文件. 那么只需要把 `sha1` 的内容 copy 到 `ems/topic/release`, 然后 nginx /openresty serve `ems/topic/release` 这个目录, 就可以上线 `sha1` 这个版本的静态代码. 如果需要切换版本(更新或者回滚), 只需要把 `sha2`, `sha3` 的内容 copy 到 `ems/topic/release`.
	
	对应目录下会写 `_pre`, `_release` 等 tag 命名的文件夹, 内容就是对应的 git hash 值, 表示这个 tag 里是这个 hash.

## Serve 的目录需要配置啥

1. 现在用 mfs 做目录, 这样可以跨机器共享一份文件.
2. 需要设定一个 `BASE_DIR`, 作为所有内容的第一级存储, 例如 `/mnt/mfs/fe`.
3. `BASE_DIR` 下写一个 `_all` 的文件, 里面就是所有可以使用的 appname, 一行一个, 这样才方便在界面上显示现在有哪些 app, 线上版本是哪些.
4. 经过上面的配置, 目录结构会是这样:

	```
	/mnt/mfs/fe/
		- _all
		- ems/topic/
			- _release
			- release/
			- 1397a3ffc49778305047b87781f6e632384251ff/
			- 5948ac24d00a12dc14317fe36ee84c7161516a3c/
			- 78016579d50508e43613faa35538ebb53a51b71c/
		- ems/test/
			_ _pre
			- pre/
			- c3901a6381f4ee35efd0f32a8fd97661e6f11ffd/
			- 8f448d393ba2bce43bd6630f784bea984a0b5d0e/
			- cd180ac844d6e16cc3549a024066f9c735926ed1/
		- bento/
			_ _release
			_ _pre
			- release/
			- pre/
			- 875dc26b70ff539614c8b582aeb6bf2935ac7637/
			- 32082a09e7d27587e9508e82523dcc80345421f2/
	```
	
	_all 里内容是 `ems/topic`, `ems/test`, `bento`, 一行一个.

## 介绍下这货里的一些 model 吧
1. **App**:
	
	一个 app 就是出现在 `BASE_DIR/_all` 里的一个名字. 他的对应路径是 `BASE_DIR/:appname`, 他的文件夹里面的内容就是 `release` 软链和全部的以 git hash 值命名的文件夹. 所以这里可以看到, appname 其实不一定是一个只有字母数字的字符串, 还可以带有 `/`, 作为子应用的分隔. 例如 `ems/topic`, `ems/test` 等.
	
2. **Version**:

	一个 version 就是一个 app 里对应的版本. 他的路径是 `BASE_DIR/:appname/:sha`, 他里面的内容就是根据仓库根目录 `rules` 文件指定的规则 copy 过来的文件, 一般这里就可以作为 nginx / openresty 的 serve root 了. 他的上下线和切换版本的方法, 就是把特定的 git hash 值的文件夹里的内容给 copy 到  `release` 这个特殊的版本里.

## TODO

- [ ]需要登录鉴权, 不能谁都瞎发布吧...
- [ ]需要给个目录丢所有的项目, 不要用 tempfile 了, 这样可以增量更新, 加快编译速度.