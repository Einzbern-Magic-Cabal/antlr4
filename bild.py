#!/usr/bin/env python
import os
import string

"""
This script uses my experimental build tool http://www.bildtool.org

In order to build the complete ANTLR4 product with Java, CSharp, Python 2/3, and JavaScript
targets, do the following from a UNIX command line.  Windows build using this script
is not yet supported. Please use the mvn build or ant build.

You will also need python 2.7, python 3.4, node.js and mono (on Mac/Linux)

!!!You must set path values in test_properties dictionary below to ensure non Java targets tests run.!!!

mkdir -p /usr/local/antlr # somewhere appropriate where you want to install stuff
cd /usr/local/antlr
git clone git@github.com:antlr/antlr4.git
git clone git@github.com:antlr/antlr4-python3.git
git clone git@github.com:antlr/antlr4-python2.git
git clone git@github.com:antlr/antlr4-csharp.git
git clone git@github.com:antlr/antlr4-javascript.git
cd antlr4
./bild.py tests
"""

# bootstrap by downloading bilder.py if not found
import urllib
import os

if not os.path.exists("bilder.py"):
    print "bootstrapping; downloading bilder.py"
    urllib.urlretrieve(
        "https://raw.githubusercontent.com/parrt/bild/master/src/python/bilder.py",
        "bilder.py")

# assumes bilder.py is in current directory
from bilder import *

BOOTSTRAP_VERSION = "4.4"
VERSION = "4.5"
JAVA_TARGET = "."
PYTHON2_TARGET = "../antlr4-python2"
PYTHON3_TARGET = "../antlr4-python3"
CSHARP_TARGET = "../antlr4-csharp"
JAVASCRIPT_TARGET = "../antlr4-javascript"

# Properties needed to run Python[23] tests
test_properties = {
"antlr-python2-runtime": uniformpath(PYTHON2_TARGET) + "/src",
"antlr-python3-runtime": uniformpath(PYTHON3_TARGET) + "/src",
"antlr-javascript-runtime": uniformpath(JAVASCRIPT_TARGET) + "/src",
"antlr-csharp-runtime-project": uniformpath(CSHARP_TARGET) + "/runtime/CSharp/Antlr4.Runtime/Antlr4.Runtime.mono.csproj"
}

TARGETS = {
            "Java": uniformpath(JAVA_TARGET),
            "CSharp":uniformpath(CSHARP_TARGET),
            "Python2": uniformpath(PYTHON2_TARGET),
            "Python3": uniformpath(PYTHON3_TARGET),
            "JavaScript":uniformpath(JAVASCRIPT_TARGET)
}


def parsers():
    antlr3("tool/src/org/antlr/v4/parse", "gen3", package="org.antlr.v4.parse")
    antlr3("tool/src/org/antlr/v4/codegen", "gen3", package="org.antlr.v4.codegen",
           args=["-lib", uniformpath("gen3/org/antlr/v4/parse")])
    antlr4("runtime/Java/src/org/antlr/v4/runtime/tree/xpath", "gen4",
           version=BOOTSTRAP_VERSION, package="org.antlr.v4.runtime.tree.xpath")

def compile():
    require(parsers)
    cp = uniformpath("out") + os.pathsep + \
         os.path.join(JARCACHE, "antlr-3.5.1-complete.jar") + os.pathsep + \
         "runtime/Java/lib/org.abego.treelayout.core.jar" + os.pathsep
    srcpath = ["gen3", "gen4", "runtime/JavaAnnotations/src", "runtime/Java/src", "tool/src"]
    args = ["-Xlint", "-Xlint:-serial", "-g", "-sourcepath", string.join(srcpath, os.pathsep)]
    for sp in srcpath:
        javac(sp, "out", version="1.6", cp=cp, args=args)
    # pull in targets
    for t in TARGETS:
        javac(TARGETS[t] + "/tool/src", "out", version="1.6", cp=cp, args=args)


def mkjar_complete():
    require(compile)
    copytree(src="tool/resources", trg="out")  # messages, Java code gen, etc...
    manifest = \
        "Main-Class: org.antlr.v4.Tool\n" +\
        "Implementation-Title: ANTLR 4 Tool\n" +\
        "Implementation-Version: %s\n" +\
        "Implementation-Vendor: ANTLR\n" +\
        "Implementation-Vendor-Id: org.antlr\n" +\
        "Built-By: %s\n" +\
        "Build-Jdk: 1.6\n" +\
        "Created-By: http://www.bildtool.org\n" +\
        "\n"
    manifest = manifest % (VERSION, os.getlogin())
    # unjar required libraries
    unjar("runtime/Java/lib/org.abego.treelayout.core.jar", trgdir="out")
    download("http://www.antlr3.org/download/antlr-3.5.1-runtime.jar", JARCACHE)
    unjar(os.path.join(JARCACHE, "antlr-3.5.1-runtime.jar"), trgdir="out")
    download("http://www.stringtemplate.org/download/ST-4.0.8.jar", JARCACHE)
    unjar(os.path.join(JARCACHE, "ST-4.0.8.jar"), trgdir="out")
    # pull in target templates
    for t in TARGETS:
        trgdir = "out/org/antlr/v4/tool/templates/codegen/" + t
        mkdir(trgdir)
        copyfile(TARGETS[t] + "/tool/resources/org/antlr/v4/tool/templates/codegen/" + t + "/" + t + ".stg",
                 trgdir)
    jarfile = "dist/antlr4-" + VERSION + "-complete.jar"
    jar(jarfile, srcdir="out", manifest=manifest)
    print "Generated " + jarfile


def mkjar_runtime():
    # out/... dir is full of tool-related stuff, make special dir out/runtime
    # unjar required library
    unjar("runtime/Java/lib/org.abego.treelayout.core.jar", trgdir="out/runtime")
    cp = uniformpath("out/runtime") + os.pathsep + \
         "runtime/Java/lib/org.abego.treelayout.core.jar"
    srcpath = ["gen4", "runtime/JavaAnnotations/src", "runtime/Java/src"]
    args = ["-nowarn", "-Xlint", "-Xlint:-serial", "-g", "-sourcepath", string.join(srcpath, os.pathsep)]
    for sp in srcpath:
        javac(sp, "out/runtime", version="1.6", cp=cp, args=args)
    manifest = \
        "Implementation-Vendor: ANTLR\n" +\
        "Implementation-Vendor-Id: org.antlr\n" +\
        "Implementation-Title: ANTLR 4 Runtime\n" +\
        "Implementation-Version: %s\n" +\
        "Built-By: %s\n" +\
        "Build-Jdk: 1.6\n" +\
        "Created-By: http://www.bildtool.org\n" +\
        "\n"
    manifest = manifest % (VERSION, os.getlogin())
    jarfile = "dist/antlr4-" + VERSION + ".jar"
    jar(jarfile, srcdir="out/runtime", manifest=manifest)
    print "Generated " + jarfile

def mkjar():
    mkjar_complete()
    # put it in JARCARCHE too so bild can find it during antlr4()
    copyfile(src="dist/antlr4-" + VERSION + "-complete.jar", trg=JARCACHE+"/antlr-"+VERSION+"-complete.jar") # note mvn wants antlr4-ver-... but I want antlr-ver-...
    # rebuild/bootstrap XPath with this version so it can use current runtime (gen'd with previous ANTLR at this point)
    rmdir("gen4/org/antlr/v4/runtime/tree/xpath")  # kill previous-version-generated code
    antlr4("runtime/Java/src/org/antlr/v4/runtime/tree/xpath", "gen4", version=VERSION,
           package="org.antlr.v4.runtime.tree.xpath")
    mkjar_complete()  # make it again with up to date XPath lexer
    mkjar_runtime()   # now build the runtime jar


def tests():
    require(mkjar)
    junit_jar, hamcrest_jar = load_junitjars()
    cp = uniformpath("dist/antlr4-" + VERSION + "-complete.jar") \
         + os.pathsep + uniformpath("out/test/Java") \
         + os.pathsep + junit_jar \
         + os.pathsep + hamcrest_jar
    juprops = ["-D%s=%s" % (p, test_properties[p]) for p in test_properties]
    args = ["-nowarn", "-Xlint", "-Xlint:-serial", "-g"]
    # don't compile generator
    skip = [ uniformpath(TARGETS['Java'] + "/tool/test/org/antlr/v4/test/rt/gen/") ]
    javac("tool/test", "out/test/Java", version="1.6", cp=cp, args=args, skip=skip)  # all targets can use org.antlr.v4.test.*
    for t in TARGETS:
        print "Testing %s ..." % t
        try:
            test(t, cp, juprops, args)
            print t + " tests complete"
        except:
            print t + " tests failed"

def test(t, cp, juprops, args):
    srcdir = uniformpath(TARGETS[t] + "/tool/test")
    dstdir = uniformpath( "out/test/" + t)
    # Prefix CLASSPATH with individual target tests
    thiscp = dstdir + os.pathsep + cp
    skip = []
    if t=='Java':
        # don't test generator
        skip = [ "/org/antlr/v4/test/rt/gen/", "TestPerformance" ]
    elif t=='Python2':
        # need BaseTest located in Py3 target
        base = uniformpath(TARGETS['Python3'] + "/tool/test")
        skip = [ "/org/antlr/v4/test/rt/py3/" ]
        javac(base, "out/test/" + t, version="1.6", cp=thiscp, args=args, skip=skip)
        skip = []
    elif t=='JavaScript':
        # don't test browsers automatically, this is overkilling and unreliable
        browsers = ["safari","chrome","firefox","explorer"]
        skip = [ uniformpath(srcdir + "/org/antlr/v4/test/rt/js/" + b) for b in  browsers ]
    javac(srcdir, "out/test/" + t, version="1.6", cp=thiscp, args=args, skip=skip)
    # copy resource files required for testing
    files = allfiles(srcdir)
    for src in files:
        if not ".java" in src and not ".stg" in src and not ".DS_Store" in src:
            dst = src.replace(srcdir, uniformpath("out/test/" + t))
            # only copy files from test dirs
            if os.path.exists(os.path.split(dst)[0]):
                shutil.copyfile(src, dst)
    junit("out/test/" + t, cp=thiscp, verbose=False, args=juprops)

def all():
    clean(True)
    mkjar()
    tests()
    mkdoc()
    mksrc()
    install()
    clean()

def install():
    mvn_install("dist/antlr4-" + VERSION + "-complete.jar",
        "dist/antlr4-" + VERSION + "-complete-sources.jar",
        "dist/antlr4-" + VERSION + "-complete-javadoc.jar",
        "org.antlr",
        "antlr4",
        VERSION)
    mvn_install("dist/antlr4-" + VERSION + ".jar",
        "dist/antlr4-" + VERSION + "-sources.jar",
        "dist/antlr4-" + VERSION + "-javadoc.jar",
        "org.antlr",
        "antlr4-runtime",
        VERSION)

def clean(dist=False):
    if dist:
        rmdir("dist")
    rmdir("out")
    rmdir("gen3")
    rmdir("gen4")
    rmdir("doc")


def mksrc():
    srcpath = "runtime/Java/src/org"
    jarfile = "dist/antlr4-" + VERSION + "-sources.jar"
    zip(jarfile, srcpath)
    print "Generated " + jarfile
    jarfile = "dist/antlr4-" + VERSION + "-complete-sources.jar"
    srcpaths = [ srcpath, "gen3/org", "gen4/org", "runtime/JavaAnnotations/src/org", "tool/src/org"]
    zip(jarfile, srcpaths)
    print "Generated " + jarfile


def mkdoc():
    # add a few source dirs to reduce the number of javadoc errors
    # JavaDoc needs antlr annotations source code
    mkdir("out/Annotations")
    download("http://search.maven.org/remotecontent?filepath=org/antlr/antlr4-annotations/4.3/antlr4-annotations-4.3-sources.jar", "out/Annotations")
    unjar("out/Annotations/antlr4-annotations-4.3-sources.jar", trgdir="out/Annotations")
    # JavaDoc needs abego treelayout source code
    mkdir("out/TreeLayout")
    download("http://search.maven.org/remotecontent?filepath=org/abego/treelayout/org.abego.treelayout.core/1.0.1/org.abego.treelayout.core-1.0.1-sources.jar", "out/TreeLayout")
    unjar("out/TreeLayout/org.abego.treelayout.core-1.0.1-sources.jar", trgdir="out/TreeLayout")
    # JavaDoc needs antlr runtime 3.5.2 source code
    mkdir("out/Antlr352Runtime")
    download("http://search.maven.org/remotecontent?filepath=org/antlr/antlr-runtime/3.5.2/antlr-runtime-3.5.2-sources.jar", "out/Antlr352Runtime")
    unjar("out/Antlr352Runtime/antlr-runtime-3.5.2-sources.jar", trgdir="out/Antlr352Runtime")
    # JavaDoc needs antlr ST4 source code
    mkdir("out/ST4")
    download("http://search.maven.org/remotecontent?filepath=org/antlr/ST4/4.0.8/ST4-4.0.8-sources.jar", "out/ST4")
    unjar("out/ST4/ST4-4.0.8-sources.jar", trgdir="out/ST4")
    # go!
    mkdir("doc/Java")
    mkdir("doc/JavaTool")
    dirs = ["runtime/Java/src"]
    dirs += ["out/Annotations"]
    dirs += ["out/TreeLayout"]
    exclude = ["org/antlr/runtime",
            "org/abego",
            "org/stringtemplate",
            "org/antlr/stringtemplate"]
    javadoc(srcdir=dirs, trgdir="doc/Java", packages="org.antlr.v4.runtime", exclude=exclude)
    dirs += ["gen3"]
    dirs += [TARGETS[t] + "/tool/src" for t in TARGETS]
    dirs += ["out/Antlr352Runtime"]
    dirs += ["out/ST4"]
    javadoc(srcdir=dirs, trgdir="doc/JavaTool", packages="org.antlr.v4", exclude=exclude)
    # build stack merge PredictionContext and ATNState images from DOT
    # DOT Images are in runtime/Java/src/main/dot/org/antlr/v4/runtime/atn/images/
    # Gen into E.g., doc/Java/org/antlr/v4/runtime/atn/images/SingletonMerge_DiffRootSamePar.svg
    mkdir("doc/Java/org/antlr/v4/runtime/atn/images")
    for f in glob.glob("runtime/Java/src/main/dot/org/antlr/v4/runtime/atn/images/*.dot"):
        dot(f, "doc/Java/org/antlr/v4/runtime/atn/images", format="svg")
    zip("dist/antlr4-" + VERSION + "-javadoc.jar", "doc/Java")
    zip("dist/antlr4-" + VERSION + "-complete-javadoc.jar", "doc/JavaTool")



processargs(globals())  # E.g., "python bild.py all"
