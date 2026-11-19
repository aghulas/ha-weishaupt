var W=globalThis,I=W.ShadowRoot&&(W.ShadyCSS===void 0||W.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,J=Symbol(),ce=new WeakMap,M=class{constructor(e,t,r){if(this._$cssResult$=!0,r!==J)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o,t=this.t;if(I&&e===void 0){let r=t!==void 0&&t.length===1;r&&(e=ce.get(t)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),r&&ce.set(t,e))}return e}toString(){return this.cssText}},he=n=>new M(typeof n=="string"?n:n+"",void 0,J),k=(n,...e)=>{let t=n.length===1?n[0]:e.reduce((r,s,i)=>r+(a=>{if(a._$cssResult$===!0)return a.cssText;if(typeof a=="number")return a;throw Error("Value passed to 'css' function must be a 'css' function result: "+a+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+n[i+1],n[0]);return new M(t,n,J)},pe=(n,e)=>{if(I)n.adoptedStyleSheets=e.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(let t of e){let r=document.createElement("style"),s=W.litNonce;s!==void 0&&r.setAttribute("nonce",s),r.textContent=t.cssText,n.appendChild(r)}},Q=I?n=>n:n=>n instanceof CSSStyleSheet?(e=>{let t="";for(let r of e.cssRules)t+=r.cssText;return he(t)})(n):n;var{is:qe,defineProperty:Le,getOwnPropertyDescriptor:Ue,getOwnPropertyNames:ze,getOwnPropertySymbols:We,getPrototypeOf:Ie}=Object,V=globalThis,fe=V.trustedTypes,Ve=fe?fe.emptyScript:"",Be=V.reactiveElementPolyfillSupport,T=(n,e)=>n,X={toAttribute(n,e){switch(e){case Boolean:n=n?Ve:null;break;case Object:case Array:n=n==null?n:JSON.stringify(n)}return n},fromAttribute(n,e){let t=n;switch(e){case Boolean:t=n!==null;break;case Number:t=n===null?null:Number(n);break;case Object:case Array:try{t=JSON.parse(n)}catch{t=null}}return t}},_e=(n,e)=>!qe(n,e),me={attribute:!0,type:String,converter:X,reflect:!1,useDefault:!1,hasChanged:_e};Symbol.metadata??=Symbol("metadata"),V.litPropertyMetadata??=new WeakMap;var y=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=me){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){let r=Symbol(),s=this.getPropertyDescriptor(e,r,t);s!==void 0&&Le(this.prototype,e,s)}}static getPropertyDescriptor(e,t,r){let{get:s,set:i}=Ue(this.prototype,e)??{get(){return this[t]},set(a){this[t]=a}};return{get:s,set(a){let l=s?.call(this);i?.call(this,a),this.requestUpdate(e,l,r)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??me}static _$Ei(){if(this.hasOwnProperty(T("elementProperties")))return;let e=Ie(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(T("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(T("properties"))){let t=this.properties,r=[...ze(t),...We(t)];for(let s of r)this.createProperty(s,t[s])}let e=this[Symbol.metadata];if(e!==null){let t=litPropertyMetadata.get(e);if(t!==void 0)for(let[r,s]of t)this.elementProperties.set(r,s)}this._$Eh=new Map;for(let[t,r]of this.elementProperties){let s=this._$Eu(t,r);s!==void 0&&this._$Eh.set(s,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){let t=[];if(Array.isArray(e)){let r=new Set(e.flat(1/0).reverse());for(let s of r)t.unshift(Q(s))}else e!==void 0&&t.push(Q(e));return t}static _$Eu(e,t){let r=t.attribute;return r===!1?void 0:typeof r=="string"?r:typeof e=="string"?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),this.renderRoot!==void 0&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){let e=new Map,t=this.constructor.elementProperties;for(let r of t.keys())this.hasOwnProperty(r)&&(e.set(r,this[r]),delete this[r]);e.size>0&&(this._$Ep=e)}createRenderRoot(){let e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return pe(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,r){this._$AK(e,r)}_$ET(e,t){let r=this.constructor.elementProperties.get(e),s=this.constructor._$Eu(e,r);if(s!==void 0&&r.reflect===!0){let i=(r.converter?.toAttribute!==void 0?r.converter:X).toAttribute(t,r.type);this._$Em=e,i==null?this.removeAttribute(s):this.setAttribute(s,i),this._$Em=null}}_$AK(e,t){let r=this.constructor,s=r._$Eh.get(e);if(s!==void 0&&this._$Em!==s){let i=r.getPropertyOptions(s),a=typeof i.converter=="function"?{fromAttribute:i.converter}:i.converter?.fromAttribute!==void 0?i.converter:X;this._$Em=s;let l=a.fromAttribute(t,i.type);this[s]=l??this._$Ej?.get(s)??l,this._$Em=null}}requestUpdate(e,t,r,s=!1,i){if(e!==void 0){let a=this.constructor;if(s===!1&&(i=this[e]),r??=a.getPropertyOptions(e),!((r.hasChanged??_e)(i,t)||r.useDefault&&r.reflect&&i===this._$Ej?.get(e)&&!this.hasAttribute(a._$Eu(e,r))))return;this.C(e,t,r)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(e,t,{useDefault:r,reflect:s,wrapped:i},a){r&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,a??t??this[e]),i!==!0||a!==void 0)||(this._$AL.has(e)||(this.hasUpdated||r||(t=void 0),this._$AL.set(e,t)),s===!0&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}let e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[s,i]of this._$Ep)this[s]=i;this._$Ep=void 0}let r=this.constructor.elementProperties;if(r.size>0)for(let[s,i]of r){let{wrapped:a}=i,l=this[s];a!==!0||this._$AL.has(s)||l===void 0||this.C(s,void 0,i,l)}}let e=!1,t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(r=>r.hostUpdate?.()),this.update(t)):this._$EM()}catch(r){throw e=!1,this._$EM(),r}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(e){}firstUpdated(e){}};y.elementStyles=[],y.shadowRootOptions={mode:"open"},y[T("elementProperties")]=new Map,y[T("finalized")]=new Map,Be?.({ReactiveElement:y}),(V.reactiveElementVersions??=[]).push("2.1.2");var ne=globalThis,ge=n=>n,B=ne.trustedTypes,ye=B?B.createPolicy("lit-html",{createHTML:n=>n}):void 0,Ae="$lit$",v=`lit$${Math.random().toFixed(9).slice(2)}$`,Ee="?"+v,Fe=`<${Ee}>`,A=document,j=()=>A.createComment(""),O=n=>n===null||typeof n!="object"&&typeof n!="function",ie=Array.isArray,Ke=n=>ie(n)||typeof n?.[Symbol.iterator]=="function",Z=`[ 	
\f\r]`,H=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,be=/-->/g,ve=/>/g,w=RegExp(`>|${Z}(?:([^\\s"'>=/]+)(${Z}*=${Z}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),$e=/'/g,we=/"/g,Se=/^(?:script|style|textarea|title)$/i,ae=n=>(e,...t)=>({_$litType$:n,strings:e,values:t}),f=ae(1),st=ae(2),nt=ae(3),E=Symbol.for("lit-noChange"),m=Symbol.for("lit-nothing"),xe=new WeakMap,x=A.createTreeWalker(A,129);function ke(n,e){if(!ie(n)||!n.hasOwnProperty("raw"))throw Error("invalid template strings array");return ye!==void 0?ye.createHTML(e):e}var Ye=(n,e)=>{let t=n.length-1,r=[],s,i=e===2?"<svg>":e===3?"<math>":"",a=H;for(let l=0;l<t;l++){let o=n[l],c,p,d=-1,h=0;for(;h<o.length&&(a.lastIndex=h,p=a.exec(o),p!==null);)h=a.lastIndex,a===H?p[1]==="!--"?a=be:p[1]!==void 0?a=ve:p[2]!==void 0?(Se.test(p[2])&&(s=RegExp("</"+p[2],"g")),a=w):p[3]!==void 0&&(a=w):a===w?p[0]===">"?(a=s??H,d=-1):p[1]===void 0?d=-2:(d=a.lastIndex-p[2].length,c=p[1],a=p[3]===void 0?w:p[3]==='"'?we:$e):a===we||a===$e?a=w:a===be||a===ve?a=H:(a=w,s=void 0);let _=a===w&&n[l+1].startsWith("/>")?" ":"";i+=a===H?o+Fe:d>=0?(r.push(c),o.slice(0,d)+Ae+o.slice(d)+v+_):o+v+(d===-2?l:_)}return[ke(n,i+(n[t]||"<?>")+(e===2?"</svg>":e===3?"</math>":"")),r]},N=class n{constructor({strings:e,_$litType$:t},r){let s;this.parts=[];let i=0,a=0,l=e.length-1,o=this.parts,[c,p]=Ye(e,t);if(this.el=n.createElement(c,r),x.currentNode=this.el.content,t===2||t===3){let d=this.el.content.firstChild;d.replaceWith(...d.childNodes)}for(;(s=x.nextNode())!==null&&o.length<l;){if(s.nodeType===1){if(s.hasAttributes())for(let d of s.getAttributeNames())if(d.endsWith(Ae)){let h=p[a++],_=s.getAttribute(d).split(v),b=/([.?@])?(.*)/.exec(h);o.push({type:1,index:i,name:b[2],strings:_,ctor:b[1]==="."?ee:b[1]==="?"?te:b[1]==="@"?re:R}),s.removeAttribute(d)}else d.startsWith(v)&&(o.push({type:6,index:i}),s.removeAttribute(d));if(Se.test(s.tagName)){let d=s.textContent.split(v),h=d.length-1;if(h>0){s.textContent=B?B.emptyScript:"";for(let _=0;_<h;_++)s.append(d[_],j()),x.nextNode(),o.push({type:2,index:++i});s.append(d[h],j())}}}else if(s.nodeType===8)if(s.data===Ee)o.push({type:2,index:i});else{let d=-1;for(;(d=s.data.indexOf(v,d+1))!==-1;)o.push({type:7,index:i}),d+=v.length-1}i++}}static createElement(e,t){let r=A.createElement("template");return r.innerHTML=e,r}};function C(n,e,t=n,r){if(e===E)return e;let s=r!==void 0?t._$Co?.[r]:t._$Cl,i=O(e)?void 0:e._$litDirective$;return s?.constructor!==i&&(s?._$AO?.(!1),i===void 0?s=void 0:(s=new i(n),s._$AT(n,t,r)),r!==void 0?(t._$Co??=[])[r]=s:t._$Cl=s),s!==void 0&&(e=C(n,s._$AS(n,e.values),s,r)),e}var G=class{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){let{el:{content:t},parts:r}=this._$AD,s=(e?.creationScope??A).importNode(t,!0);x.currentNode=s;let i=x.nextNode(),a=0,l=0,o=r[0];for(;o!==void 0;){if(a===o.index){let c;o.type===2?c=new D(i,i.nextSibling,this,e):o.type===1?c=new o.ctor(i,o.name,o.strings,this,e):o.type===6&&(c=new se(i,this,e)),this._$AV.push(c),o=r[++l]}a!==o?.index&&(i=x.nextNode(),a++)}return x.currentNode=A,s}p(e){let t=0;for(let r of this._$AV)r!==void 0&&(r.strings!==void 0?(r._$AI(e,r,t),t+=r.strings.length-2):r._$AI(e[t])),t++}},D=class n{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,r,s){this.type=2,this._$AH=m,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=r,this.options=s,this._$Cv=s?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode,t=this._$AM;return t!==void 0&&e?.nodeType===11&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=C(this,e,t),O(e)?e===m||e==null||e===""?(this._$AH!==m&&this._$AR(),this._$AH=m):e!==this._$AH&&e!==E&&this._(e):e._$litType$!==void 0?this.$(e):e.nodeType!==void 0?this.T(e):Ke(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==m&&O(this._$AH)?this._$AA.nextSibling.data=e:this.T(A.createTextNode(e)),this._$AH=e}$(e){let{values:t,_$litType$:r}=e,s=typeof r=="number"?this._$AC(e):(r.el===void 0&&(r.el=N.createElement(ke(r.h,r.h[0]),this.options)),r);if(this._$AH?._$AD===s)this._$AH.p(t);else{let i=new G(s,this),a=i.u(this.options);i.p(t),this.T(a),this._$AH=i}}_$AC(e){let t=xe.get(e.strings);return t===void 0&&xe.set(e.strings,t=new N(e)),t}k(e){ie(this._$AH)||(this._$AH=[],this._$AR());let t=this._$AH,r,s=0;for(let i of e)s===t.length?t.push(r=new n(this.O(j()),this.O(j()),this,this.options)):r=t[s],r._$AI(i),s++;s<t.length&&(this._$AR(r&&r._$AB.nextSibling,s),t.length=s)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){let r=ge(e).nextSibling;ge(e).remove(),e=r}}setConnected(e){this._$AM===void 0&&(this._$Cv=e,this._$AP?.(e))}},R=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,r,s,i){this.type=1,this._$AH=m,this._$AN=void 0,this.element=e,this.name=t,this._$AM=s,this.options=i,r.length>2||r[0]!==""||r[1]!==""?(this._$AH=Array(r.length-1).fill(new String),this.strings=r):this._$AH=m}_$AI(e,t=this,r,s){let i=this.strings,a=!1;if(i===void 0)e=C(this,e,t,0),a=!O(e)||e!==this._$AH&&e!==E,a&&(this._$AH=e);else{let l=e,o,c;for(e=i[0],o=0;o<i.length-1;o++)c=C(this,l[r+o],t,o),c===E&&(c=this._$AH[o]),a||=!O(c)||c!==this._$AH[o],c===m?e=m:e!==m&&(e+=(c??"")+i[o+1]),this._$AH[o]=c}a&&!s&&this.j(e)}j(e){e===m?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}},ee=class extends R{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===m?void 0:e}},te=class extends R{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==m)}},re=class extends R{constructor(e,t,r,s,i){super(e,t,r,s,i),this.type=5}_$AI(e,t=this){if((e=C(this,e,t,0)??m)===E)return;let r=this._$AH,s=e===m&&r!==m||e.capture!==r.capture||e.once!==r.once||e.passive!==r.passive,i=e!==m&&(r===m||s);s&&this.element.removeEventListener(this.name,this,r),i&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}},se=class{constructor(e,t,r){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=r}get _$AU(){return this._$AM._$AU}_$AI(e){C(this,e)}};var Je=ne.litHtmlPolyfillSupport;Je?.(N,D),(ne.litHtmlVersions??=[]).push("3.3.3");var Ce=(n,e,t)=>{let r=t?.renderBefore??e,s=r._$litPart$;if(s===void 0){let i=t?.renderBefore??null;r._$litPart$=s=new D(e.insertBefore(j(),i),i,void 0,t??{})}return s._$AI(n),s};var oe=globalThis,g=class extends y{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){let t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=Ce(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return E}};g._$litElement$=!0,g.finalized=!0,oe.litElementHydrateSupport?.({LitElement:g});var Qe=oe.litElementPolyfillSupport;Qe?.({LitElement:g});(oe.litElementVersions??=[]).push("4.2.2");var le={en:{title:"Weishaupt",installation:"Installation",devices:"Devices",definitions:"Definitions",programs:"Weekly programs",loading:"Loading\u2026",no_installation:"No Weishaupt installation is loaded.",unavailable:"ebusd does not answer: the values shown are the last ones read.",value:"Value",name:"Name",age:"Read",range:"Range",write:"Write",entity:"Entity",open:"Open",comfort:"comfort",regulation:"regulation",read_only:"read only",not_loaded:"not loaded by ebusd",not_listened:"not read: no enabled entity",waiting:"waiting for the first reading",not_available:"not available",seconds_ago:"{n} s ago",minutes_ago:"{n} min ago",hours_ago:"{n} h ago",days_ago:"{n} d ago",passive:"sent by the device",clock_offset:"Clock master",clock_line:"{label}: {text}",clock_ahead:"{n} s ahead",clock_behind:"{n} s behind",clock_on_time:"on time",software:"Software",hardware:"Hardware",address:"Bus address",in_use:"In use",source_bundled:"shipped with the integration",source_file:"file beside the configuration: {file}",refused:"Files not used",mismatches:"Differences with ebusd",named_from_metadata:"Entities named from the definitions",not_named:"Entities waiting for a name",messages:"Messages",usable:"{usable} of {messages} loaded by ebusd as described",writes:"Writes",writes_off:"disabled in the options",switch_on:"switch on",switch_off:"switch off",capability:"run-time checksum: {value}",per_hour:"{n} of {max} this hour",ebusd:"ebusd",unknown_addresses:"Addresses answering that no definition knows",none:"none",day_unread:"not read yet",day_none:"no range",editable:"editable through its program-day entities",not_editable:"read only: not proven writable on this device",not_read_program:"not loaded by ebusd",program_not_listened:"not read by any enabled entity: read it once now, or enable the program sensor to keep it up to date",write_hint:"Change a setting with its button Change (the writes switch must be on). Comfort: written at once and read back; regulation: after a confirmation in this panel. Open shows the entity.",description:"Description",no_sensor:"no sensor",kept:"kept from before the reload, read again soon",through:"through {circuit}",read_now:"Read now",read_cost:"{n} requests to the bus, about {s} s, once",read_queued:"{n} requests queued; the grid fills in as they are answered",readable:"{usable} of {readable} readable messages loaded by ebusd as described",not_usable:"Messages not read",reason_write_only:"write only",reason_device_absent:"device not on the bus",absent_circuit:"{circuit}: {n} messages, device not on the bus",reason_mismatch:"not loaded as described",reason_other:"not read",disabled:"disabled",reloading:"The integration was reloaded: loading again\u2026",read_only_settings:"Settings left read-only",edit:"Change",write_now:"Write",cancel:"Cancel",confirm:"Write to the controller",confirm_clock:"Send the time",confirm_title:"Confirm: {setting} \u2014 {device}",current:"Current value",new_value:"New value",allowed:"Allowed",path:"Written to bus address {address}, register {register}, from source address {source} ({source_text}). Read back right after.",path_short:"bus address {address}, register {register}, from {source}",regulation_note:"This setting changes how the heating is regulated: it is written after your confirmation.",comfort_note:"Comfort setting: written at once and read back.",writing:"Writing\u2026",written_line:"{before} \u2192 {after}{frame}: {result}",not_written:"Not written: {message}",not_offered_writes_disabled:"writes are not enabled in the options",not_offered:"not offered on this installation: {reason}",switch_off_hint:"The writes switch is off: turn it on to write.",edit_days:"Edit",write_days:"Write the changed days",discard:"Discard changes",copy_to:"Copy to",copy:"Copy",cost:"{days} days changed: up to {writes} writes (only changed slots are written); {used} of {max} this hour",cost_one:"1 day changed: up to {writes} writes (only changed slots are written); {used} of {max} this hour",interrupted:"no answer from Home Assistant (connection interrupted): the write may or may not have been sent; check the value read back",drag_hint:"Type the ranges, or drag on the bar to add one in quarters of an hour; a click on a range removes it.",day_format:"use HH:MM-HH:MM, up to three ranges, or -",day_quarter:"times must be quarters of an hour, from 00:00 to 24:00",day_order:"a range must end after it starts",day_too_many:"at most three ranges",day_overlap:"ranges must not overlap",set_clock:"Set the clock",clock_confirm:"Will send Home Assistant's time at second 00 of the next minute ({send_at}), to bus address fe from source address 31. If the bus is not free within {late} s of second 00, nothing is sent.",clock_sent:"Sent {requested} ({frame}): {result}",clock_current:"Clock master now: {current}",col_device:"Device",col_menu:"Menu",col_label:"Setting",col_value:"Value",col_unit:"Unit",col_range:"Range (step) or choices",col_writable:"Writable",report:"Printable report",export_csv:"Export CSV",report_title:"Settings of the installation",report_subtitle:"{date} \xB7 definitions {version} \xB7 read by the Weishaupt integration of Home Assistant",report_no_factory:"Factory values: the definitions do not carry them yet. An empty value was not read when the report was made.",report_blocked:"The browser blocked the report window: allow pop-ups for Home Assistant and try again.",faults:"Faults",fault_history:"Fault history",fault_counters:"Fault counters",fault_log:"Fault log of the system manager (selected entry)",fault_code:"Code",fault_text:"Text",fault_slot:"Slot",fault_values:"Values stored with it",fault_number:"Fault",fault_count:"Count",fault_none:"no fault stored",fault_unordered:"Order unknown: the pointer to the last entry is not read.",fault_no_time:"The boiler stores no time with an entry.",fault_log_fields:"Entry {id}: code {code}, type {type}, origin {device}, {time}",fault_log_hint:"The operating unit of the system manager selects the entry shown; selecting another one is a write, which the panel does not do.",faults_unread:"{n} of these messages are read by no enabled entity.",faults_read_once:"Read once on demand: not kept up to date unless their entities are enabled.",read_nothing:"Nothing to request: these messages are already read by enabled entities or waiting.",card_name:"Weishaupt weekly program",card_description:"The week grid of one weekly program of a Weishaupt controller.",card_no_entity:"Choose a program sensor of the Weishaupt integration in the card's settings.",card_missing:"{entity} does not exist, or is disabled: enable it in Settings \u2192 Entities (program sensors are created disabled).",card_unavailable:"{entity} is unavailable: ebusd or the controller does not answer.",card_unread:"not read yet",card_editor_entity:"Program sensor",card_editor_title:"Title (optional)",card_editor_today:"Mark today",card_edit:"Edit",card_type_hint:"Type up to three ranges a day, HH:MM-HH:MM, or - for none; only changed days are written.",card_edit_admin:"Days are changed by administrators, here or in the Weishaupt panel.",card_not_writable:"This program is not proven writable on its device: read only.",card_writing_day:"{day}: writing\u2026",card_written_day:"{day}: written and read back",card_failed_day:"{day}: not written: {message}",card_no_switch:"Writes are not enabled in the options of the integration.",read_queued_one:"1 request queued (about {s} s).",read_queued_n:"{n} requests queued (about {s} s).",read_after_first_pass:"They come after the first pass that follows a start: {n} reads still due, {wait}.",read_after_queue:"They come after {n} reads already due, {wait}.",about_s:"about {n} s",about_min:"about {n} min"},fr:{title:"Weishaupt",installation:"Installation",devices:"Appareils",definitions:"D\xE9finitions",programs:"Programmes hebdomadaires",loading:"Chargement\u2026",no_installation:"Aucune installation Weishaupt n'est charg\xE9e.",unavailable:"ebusd ne r\xE9pond pas : les valeurs affich\xE9es sont les derni\xE8res lues.",value:"Valeur",name:"Nom",age:"Lu",range:"Plage",write:"\xC9criture",entity:"Entit\xE9",open:"Ouvrir",comfort:"confort",regulation:"r\xE9gulation",read_only:"lecture seule",not_loaded:"non charg\xE9 par ebusd",not_listened:"non lu : aucune entit\xE9 activ\xE9e",waiting:"en attente de la premi\xE8re lecture",not_available:"non disponible",seconds_ago:"il y a {n} s",minutes_ago:"il y a {n} min",hours_ago:"il y a {n} h",days_ago:"il y a {n} j",passive:"envoy\xE9 par l'appareil",clock_offset:"Horloge ma\xEEtresse",clock_line:"{label} : {text}",clock_ahead:"{n} s d'avance",clock_behind:"{n} s de retard",clock_on_time:"\xE0 l'heure",software:"Logiciel",hardware:"Mat\xE9riel",address:"Adresse de bus",in_use:"Utilis\xE9es",source_bundled:"livr\xE9es avec l'int\xE9gration",source_file:"fichier \xE0 c\xF4t\xE9 de la configuration : {file}",refused:"Fichiers non utilis\xE9s",mismatches:"\xC9carts avec ebusd",named_from_metadata:"Entit\xE9s nomm\xE9es par les d\xE9finitions",not_named:"Entit\xE9s en attente d'un nom",messages:"Messages",usable:"{usable} sur {messages} charg\xE9s par ebusd comme d\xE9crits",writes:"\xC9critures",writes_off:"d\xE9sactiv\xE9es dans les options",switch_on:"interrupteur allum\xE9",switch_off:"interrupteur \xE9teint",capability:"checksum \xE0 l'ex\xE9cution : {value}",per_hour:"{n} sur {max} cette heure",ebusd:"ebusd",unknown_addresses:"Adresses qui r\xE9pondent sans d\xE9finition",none:"aucun",day_unread:"pas encore lu",day_none:"aucune plage",editable:"modifiable par ses entit\xE9s de jour de programme",not_editable:"lecture seule : \xE9criture non prouv\xE9e sur cet appareil",not_read_program:"non charg\xE9 par ebusd",program_not_listened:"lu par aucune entit\xE9 activ\xE9e : lisez-le une fois maintenant, ou activez le capteur du programme pour le tenir \xE0 jour",write_hint:"Modifiez un r\xE9glage avec son bouton Modifier (l'interrupteur d'\xE9criture doit \xEAtre allum\xE9). Confort : \xE9crit aussit\xF4t et relu ; r\xE9gulation : apr\xE8s une confirmation dans ce panneau. Ouvrir affiche l'entit\xE9.",description:"Description",no_sensor:"pas de sonde",kept:"conserv\xE9e d'avant le rechargement, relue bient\xF4t",through:"par {circuit}",read_now:"Lire maintenant",read_cost:"{n} requ\xEAtes sur le bus, environ {s} s, une seule fois",read_queued:"{n} requ\xEAtes en file ; la grille se remplit au fil des r\xE9ponses",readable:"{usable} sur {readable} messages lisibles charg\xE9s par ebusd comme d\xE9crits",not_usable:"Messages non lus",reason_write_only:"\xE9criture seule",reason_device_absent:"appareil absent du bus",absent_circuit:"{circuit} : {n} messages, appareil absent du bus",reason_mismatch:"non charg\xE9 comme d\xE9crit",reason_other:"non lu",disabled:"d\xE9sactiv\xE9e",reloading:"L'int\xE9gration a \xE9t\xE9 recharg\xE9e : nouveau chargement\u2026",read_only_settings:"R\xE9glages laiss\xE9s en lecture seule",edit:"Modifier",write_now:"\xC9crire",cancel:"Annuler",confirm:"\xC9crire dans le r\xE9gulateur",confirm_clock:"Envoyer l'heure",confirm_title:"Confirmer : {setting} \u2014 {device}",current:"Valeur actuelle",new_value:"Nouvelle valeur",allowed:"Valeurs autoris\xE9es",path:"\xC9crit \xE0 l'adresse de bus {address}, registre {register}, depuis l'adresse source {source} ({source_text}). Relu juste apr\xE8s.",path_short:"adresse de bus {address}, registre {register}, depuis {source}",regulation_note:"Ce r\xE9glage modifie la r\xE9gulation du chauffage : il est \xE9crit apr\xE8s votre confirmation.",comfort_note:"R\xE9glage de confort : \xE9crit aussit\xF4t et relu.",writing:"\xC9criture\u2026",written_line:"{before} \u2192 {after}{frame} : {result}",not_written:"Non \xE9crit : {message}",not_offered_writes_disabled:"l'\xE9criture n'est pas activ\xE9e dans les options",not_offered:"non propos\xE9 sur cette installation : {reason}",switch_off_hint:"L'interrupteur d'\xE9criture est \xE9teint : allumez-le pour \xE9crire.",edit_days:"Modifier",write_days:"\xC9crire les jours modifi\xE9s",discard:"Abandonner les modifications",copy_to:"Copier vers",copy:"Copier",cost:"{days} jours modifi\xE9s : jusqu'\xE0 {writes} \xE9critures (seuls les cr\xE9neaux chang\xE9s sont \xE9crits) ; {used} sur {max} cette heure",cost_one:"1 jour modifi\xE9 : jusqu'\xE0 {writes} \xE9critures (seuls les cr\xE9neaux chang\xE9s sont \xE9crits) ; {used} sur {max} cette heure",interrupted:"pas de r\xE9ponse de Home Assistant (connexion interrompue) : l'\xE9criture a pu partir ou non ; v\xE9rifiez la valeur relue",drag_hint:"Saisissez les plages, ou glissez sur la barre pour en ajouter une au quart d'heure ; un clic sur une plage la retire.",day_format:"\xE9crivez HH:MM-HH:MM, trois plages au plus, ou -",day_quarter:"les heures doivent \xEAtre des quarts d'heure, de 00:00 \xE0 24:00",day_order:"une plage doit finir apr\xE8s son d\xE9but",day_too_many:"trois plages au plus",day_overlap:"les plages ne doivent pas se chevaucher",set_clock:"Mettre \xE0 l'heure",clock_confirm:"Enverra l'heure de Home Assistant \xE0 la seconde 00 de la minute suivante ({send_at}), \xE0 l'adresse de bus fe depuis l'adresse source 31. Si le bus n'est pas libre dans les {late} s apr\xE8s la seconde 00, rien n'est envoy\xE9.",clock_sent:"Envoy\xE9 {requested} ({frame}) : {result}",clock_current:"Horloge ma\xEEtresse maintenant : {current}",col_device:"Appareil",col_menu:"Menu",col_label:"R\xE9glage",col_value:"Valeur",col_unit:"Unit\xE9",col_range:"Plage (pas) ou choix",col_writable:"Inscriptible",report:"Rapport imprimable",export_csv:"Exporter en CSV",report_title:"R\xE9glages de l'installation",report_subtitle:"{date} \xB7 d\xE9finitions {version} \xB7 lus par l'int\xE9gration Weishaupt de Home Assistant",report_no_factory:"Valeurs d'usine : les d\xE9finitions ne les donnent pas encore. Une valeur vide n'\xE9tait pas lue au moment du rapport.",report_blocked:"Le navigateur a bloqu\xE9 la fen\xEAtre du rapport : autorisez les fen\xEAtres pour Home Assistant et r\xE9essayez.",faults:"D\xE9fauts",fault_history:"M\xE9moire de d\xE9fauts",fault_counters:"Compteurs de d\xE9fauts",fault_log:"Journal de d\xE9fauts du manager syst\xE8me (entr\xE9e s\xE9lectionn\xE9e)",fault_code:"Code",fault_text:"Texte",fault_slot:"Emplacement",fault_values:"Valeurs enregistr\xE9es avec lui",fault_number:"D\xE9faut",fault_count:"Nombre",fault_none:"aucun d\xE9faut enregistr\xE9",fault_unordered:"Ordre inconnu : le pointeur de la derni\xE8re entr\xE9e n'est pas lu.",fault_no_time:"La chaudi\xE8re n'enregistre pas d'heure avec une entr\xE9e.",fault_log_fields:"Entr\xE9e {id} : code {code}, type {type}, origine {device}, {time}",fault_log_hint:"Le tableau de commande du manager syst\xE8me choisit l'entr\xE9e affich\xE9e ; en choisir une autre est une \xE9criture, que le panneau ne fait pas.",faults_unread:"{n} de ces messages ne sont lus par aucune entit\xE9 activ\xE9e.",faults_read_once:"Lus une fois \xE0 la demande : pas tenus \xE0 jour tant que leurs entit\xE9s ne sont pas activ\xE9es.",read_nothing:"Rien \xE0 demander : ces messages sont d\xE9j\xE0 lus par des entit\xE9s activ\xE9es ou en attente.",card_name:"Programme hebdomadaire Weishaupt",card_description:"La grille de la semaine d'un programme hebdomadaire d'un r\xE9gulateur Weishaupt.",card_no_entity:"Choisissez un capteur de programme de l'int\xE9gration Weishaupt dans les r\xE9glages de la carte.",card_missing:"{entity} n'existe pas ou est d\xE9sactiv\xE9 : activez-le dans Param\xE8tres \u2192 Entit\xE9s (les capteurs de programme sont cr\xE9\xE9s d\xE9sactiv\xE9s).",card_unavailable:"{entity} est indisponible : ebusd ou le r\xE9gulateur ne r\xE9pond pas.",card_unread:"pas encore lu",card_editor_entity:"Capteur de programme",card_editor_title:"Titre (facultatif)",card_editor_today:"Marquer aujourd'hui",card_edit:"Modifier",card_type_hint:"Saisissez jusqu'\xE0 trois plages par jour, HH:MM-HH:MM, ou - pour aucune ; seuls les jours modifi\xE9s sont \xE9crits.",card_edit_admin:"Les jours sont modifi\xE9s par les administrateurs, ici ou dans le panneau Weishaupt.",card_not_writable:"Ce programme n'est pas prouv\xE9 inscriptible sur son appareil : lecture seule.",card_writing_day:"{day} : \xE9criture\u2026",card_written_day:"{day} : \xE9crit et relu",card_failed_day:"{day} : non \xE9crit : {message}",card_no_switch:"L'\xE9criture n'est pas activ\xE9e dans les options de l'int\xE9gration.",read_queued_one:"1 requ\xEAte en file (environ {s} s).",read_queued_n:"{n} requ\xEAtes en file (environ {s} s).",read_after_first_pass:"Elles passent apr\xE8s la premi\xE8re lecture qui suit un d\xE9marrage : {n} lectures encore dues, {wait}.",read_after_queue:"Elles passent apr\xE8s {n} lectures d\xE9j\xE0 dues, {wait}.",about_s:"environ {n} s",about_min:"environ {n} min"}},$={en:["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],fr:["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]};function q(n){let e=(n??"en").split("-")[0];return e in le?e:"en"}function u(n,e,t={}){return(le[n]?.[e]??le.en[e]??e).replace(/\{(\w+)\}/g,(s,i)=>String(t[i]??`{${i}}`))}var Xe=3,Ze=15;function K(n){let e=n.trim();if(e===""||e==="-")return{ranges:[]};let t=[];for(let r of e.split(",")){let s=/^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$/.exec(r);if(!s)return{error:"day_format"};let[i,a,l,o]=s.slice(1).map(Number),c=i*60+a,p=l*60+o;if([a,o].some(d=>d%Ze)||c>1440||p>1440||a>45||o>45)return{error:"day_quarter"};if(c>=p)return{error:"day_order"};t.push([c,p])}if(t.length>Xe)return{error:"day_too_many"};t.sort((r,s)=>r[0]-s[0]);for(let r=1;r<t.length;r++)if(t[r][0]<t[r-1][1])return{error:"day_overlap"};return{ranges:t}}function F(n){let e=Math.floor(n/60),t=n%60;return`${String(e).padStart(2,"0")}:${String(t).padStart(2,"0")}`}function de(n){return n.length?n.map(([e,t])=>`${F(e)}-${F(t)}`).join(", "):"-"}function Re(n){let[e,t]=n.split(":").map(r=>Number(r));return e*60+(t||0)}function Me(n){return n.map(([e,t])=>{let r=Re(e),s=Re(t);return{left:r/1440*100,width:Math.max(0,s-r)/1440*100,text:`${e}-${t}`}})}var P=["monday","tuesday","wednesday","thursday","friday","saturday","sunday"];function Te(n){let e={};return P.forEach((t,r)=>{let s=n[t],i=typeof s=="string"?K(s):null;e[String(r+1)]=i&&"ranges"in i?i.ranges.map(([a,l])=>[F(a),F(l)]):null}),e}function He(n,e){if(!n.startsWith("sensor."))return!1;let t=P.filter(s=>typeof e[s]=="string").length,r=Object.keys(e).filter(s=>!P.includes(s)&&!["friendly_name","icon"].includes(s));return t>0&&r.length===0||t===0&&/program/.test(n)}function je(n){return(n.getDay()+6)%7+1}function Oe(n,e){let t=n?.[e];if(!n||!t?.device_id||!t.translation_key)return null;let r={};for(let s of Object.values(n)){if(s.platform!=="weishaupt"||s.device_id!==t.device_id||!s.entity_id.startsWith("text."))continue;let i=P.findIndex(a=>s.translation_key===`${t.translation_key}_${a}`);i>=0&&(r[String(i+1)]=s.entity_id)}return Object.keys(r).length===P.length?r:null}function Ne(n,e){let t=Object.values(n??{}).find(i=>i.platform==="weishaupt"&&i.translation_key==="writes"),r=t?e[t.entity_id]:void 0;if(!r)return null;let s=i=>typeof i=="number"?i:null;return{on:r.state==="on",used:s(r.attributes.writes_last_hour),max:s(r.attributes.max_writes_per_hour)}}var L=class extends g{constructor(){super(),this.language="en",this.unread="",this.today=0,this.caption=""}render(){let e=this.language,t=$[e]??$.en;return f`<table>
      ${this.caption?f`<caption class="visually-hidden">${this.caption}</caption>`:m}
      <thead>
        <tr>
          <th scope="col"><span class="visually-hidden">${u(e,"programs")}</span></th>
          <td class="scale" aria-hidden="true">
            ${[0,6,12,18,24].map(r=>f`<span style="left:${r/24*100}%">${r}</span>`)}
          </td>
        </tr>
      </thead>
      <tbody>
        ${t.map((r,s)=>{let i=this.days?.[String(s+1)],a=i==null?this.unread||u(e,"day_unread"):i.length?i.map(([l,o])=>`${l}-${o}`).join(", "):u(e,"day_none");return f`<tr class=${this.today===s+1?"today":""}>
            <th scope="row">${r}</th>
            <td>
              <div class="day" aria-hidden="true">
                ${(i??[]).length?Me(i).map(l=>f`<span class="bar" style="left:${l.left}%;width:${l.width}%"></span>`):m}
              </div>
              <div class="day-text">${a}</div>
            </td>
          </tr>`})}
      </tbody>
    </table>`}};L.properties={days:{attribute:!1},language:{type:String},unread:{type:String},today:{type:Number},caption:{type:String}},L.styles=k`
    :host {
      display: block;
    }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    th,
    td {
      text-align: start;
      vertical-align: top;
      padding: 6px 8px;
      border-bottom: 1px solid var(--divider-color);
    }
    tbody th {
      font-weight: 400;
      width: 8em;
    }
    tr.today th {
      font-weight: 500;
      color: var(--primary-color);
    }
    .scale {
      position: relative;
      height: 1.4em;
    }
    .scale span {
      position: absolute;
      transform: translateX(-50%);
      color: var(--secondary-text-color);
      font-size: 0.8em;
    }
    .day {
      position: relative;
      height: 14px;
      background: var(--secondary-background-color);
      border-radius: 4px;
    }
    .bar {
      position: absolute;
      top: 0;
      bottom: 0;
      background: var(--primary-color);
      border-radius: 4px;
    }
    .day-text {
      font-size: 0.85em;
      color: var(--secondary-text-color);
      margin-top: 2px;
    }
    .visually-hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
      white-space: nowrap;
    }
  `;customElements.get("weishaupt-week-grid")||customElements.define("weishaupt-week-grid",L);var S="weishaupt-program-card",ue="weishaupt-program-card-editor";function Pe(n){let e=t=>n.states[t].state==="unavailable"?1:0;return Object.keys(n.states).filter(t=>He(t,n.states[t].attributes)).sort((t,r)=>e(t)-e(r)||t.localeCompare(r))}var U=class extends g{constructor(){super(),this._results={},this._busy=!1}setConfig(e){if(!e||typeof e!="object")throw new Error("Invalid configuration");this._config={today:!0,...e}}getCardSize(){return 5}static getStubConfig(e){return{type:`custom:${S}`,entity:Pe(e)[0]??"",today:!0}}static getConfigElement(){return document.createElement(ue)}render(){let e=q(this.hass?.language),t=this._config??{type:S},r=t.entity,s=r?this.hass?.states[r]:void 0,i=t.title||s?.attributes.friendly_name||u(e,"card_name"),a;if(!r)a=f`<p class="message">${u(e,"card_no_entity")}</p>`;else if(!s)a=f`<p class="message">${u(e,"card_missing",{entity:r})}</p>`;else if(s.state==="unavailable")a=f`<p class="message">${u(e,"card_unavailable",{entity:r})}</p>`;else{let l=Te(s.attributes),o=this.hass.user?.is_admin?Oe(this.hass.entities,r):null;a=this._draft&&o?this._editor(l,o,e):f`<weishaupt-week-grid
              .days=${l}
              language=${e}
              unread=${u(e,"card_unread")}
              caption=${i}
              today=${t.today===!1?0:je(new Date)}
            ></weishaupt-week-grid>
            ${o?f`<div class="actions">
                  <button class="link" @click=${()=>this._start(l)}>${u(e,"card_edit")}</button>
                </div>`:null}
            ${this._resultLines()}`}return f`<div class="card"><h2>${i}</h2>${a}</div>`}_current(e,t){let r=e[t];return r?de(r.map(([s,i])=>[De(s),De(i)])):null}_start(e){let t={};for(let r=1;r<=7;r++)t[String(r)]=this._current(e,String(r))??"";this._draft=t,this._results={}}_changed(e){let t=this._draft??{};return Object.keys(t).filter(r=>{let s=this._current(e,r);if(s===null&&t[r].trim()==="")return!1;let i=K(t[r]);return("ranges"in i?de(i.ranges):t[r])!==s})}_copy(e,t){let r=this._draft[e],s=t==="all"?["1","2","3","4","5","6","7"]:t==="weekdays"?["1","2","3","4","5"]:["6","7"],i={...this._draft};for(let a of s)i[a]=r;this._draft=i}async _write(e,t){let r=q(this.hass.language),s=$[r]??$.en;this._busy=!0;let i={};for(let a of this._changed(e)){let l=s[Number(a)-1];this._results={...i,[a]:{text:u(r,"card_writing_day",{day:l}),error:!1}};try{await this.hass.callService("text","set_value",{value:this._draft[a]},{entity_id:t[a]}),i[a]={text:u(r,"card_written_day",{day:l}),error:!1}}catch(o){i[a]={text:u(r,"card_failed_day",{day:l,message:o.message??""}),error:!0}}}this._results=i,this._busy=!1,Object.values(i).some(a=>a.error)||(this._draft=void 0)}_resultLines(){let e=Object.values(this._results);return e.length?f`<div class="results" role="status">
          ${e.map(t=>f`<div class=${t.error?"error":"secondary"}>${t.text}</div>`)}
        </div>`:null}_editor(e,t,r){let s=$[r]??$.en,i=this._draft,a=this._changed(e),l=Object.fromEntries(Object.entries(i).map(([p,d])=>{let h=K(d);return[p,"error"in h?h.error:null]})),o=Object.values(l).some(Boolean),c=Ne(this.hass.entities,this.hass.states);return f`<p class="secondary">${u(r,"card_type_hint")}</p>
      ${s.map((p,d)=>{let h=String(d+1);return f`<div class=${a.includes(h)?"day changed":"day"}>
          <label for="d${h}">${p}</label>
          <input id="d${h}" type="text" .value=${i[h]} aria-invalid=${l[h]?"true":"false"}
            placeholder=${e[h]==null?u(r,"card_unread"):""}
            @input=${_=>this._draft={...i,[h]:_.target.value}} />
          <select aria-label=${u(r,"copy_to")} @change=${_=>{let b=_.target;b.value&&this._copy(h,b.value),b.value=""}}>
            <option value="">${u(r,"copy_to")}…</option>
            <option value="all">${r==="fr"?"tous les jours":"every day"}</option>
            <option value="weekdays">${r==="fr"?"lundi \u2013 vendredi":"Monday \u2013 Friday"}</option>
            <option value="weekend">${r==="fr"?"samedi, dimanche":"Saturday, Sunday"}</option>
          </select>
          ${l[h]?f`<div class="error" role="alert">${u(r,l[h])}</div>`:null}
          ${this._results[h]?f`<div class=${this._results[h].error?"error":"secondary"}>${this._results[h].text}</div>`:null}
        </div>`})}
      ${c?f`<p class="secondary">
              ${u(r,a.length===1?"cost_one":"cost",{days:a.length,writes:a.length*3,used:c.used??"?",max:c.max??"?"})}
            </p>
            ${c.on?null:f`<p class="error">${u(r,"switch_off_hint")}</p>`}`:f`<p class="error">${u(r,"card_no_switch")}</p>`}
      <div class="actions">
        <button class="link" ?disabled=${this._busy} @click=${()=>{this._draft=void 0,this._results={}}}>
          ${u(r,"discard")}
        </button>
        <button class="primary" ?disabled=${this._busy||o||!a.length}
          @click=${()=>this._write(e,t)}>${u(r,"write_days")}</button>
      </div>`}};U.properties={hass:{attribute:!1},_config:{state:!0},_draft:{state:!0},_results:{state:!0},_busy:{state:!0}},U.styles=k`
    .card {
      background: var(--ha-card-background, var(--card-background-color));
      color: var(--primary-text-color);
      border-radius: var(--ha-card-border-radius, 12px);
      border: var(--ha-card-border-width, 1px) solid var(--ha-card-border-color, var(--divider-color));
      box-shadow: var(--ha-card-box-shadow, none);
      padding: 12px 16px 16px;
    }
    h2 {
      font-size: var(--ha-card-header-font-size, 20px);
      font-weight: 400;
      margin: 0 0 8px;
    }
    .message,
    .secondary {
      color: var(--secondary-text-color);
      margin: 0;
    }
    .secondary {
      font-size: 0.9em;
    }
    .error {
      color: var(--error-color);
      font-size: 0.9em;
    }
    .day {
      display: grid;
      grid-template-columns: 6.5em minmax(0, 1fr) auto;
      gap: 4px 8px;
      align-items: center;
      padding: 6px 0;
      border-bottom: 1px solid var(--divider-color);
    }
    .day .error,
    .day .secondary {
      grid-column: 2 / -1;
    }
    .day.changed label {
      color: var(--primary-color);
      font-weight: 500;
    }
    input,
    select {
      font: inherit;
      padding: 4px 6px;
      min-width: 0;
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 6px;
    }
    input[aria-invalid="true"] {
      border-color: var(--error-color);
    }
    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      margin-top: 8px;
    }
    .results {
      margin-top: 8px;
    }
    button {
      font: inherit;
      cursor: pointer;
    }
    button.link {
      border: 1px solid var(--divider-color);
      background: none;
      border-radius: 6px;
      padding: 2px 10px;
      color: var(--primary-color);
    }
    button.primary {
      border: 0;
      border-radius: 6px;
      padding: 4px 12px;
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }
    button:disabled {
      opacity: 0.5;
      cursor: default;
    }
  `;function De(n){let[e,t]=n.split(":").map(Number);return e*60+(t||0)}var z=class extends g{setConfig(e){this._config=e}_change(e){this._config={...this._config,...e},this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:this._config},bubbles:!0,composed:!0}))}render(){let e=q(this.hass?.language),t=this.hass?Pe(this.hass):[],r=this._config??{type:`custom:${S}`};return f`<div class="editor">
      <label
        >${u(e,"card_editor_entity")}
        <select @change=${s=>this._change({entity:s.target.value})}>
          <option value="" ?selected=${!r.entity}>…</option>
          ${t.map(s=>f`<option value=${s} ?selected=${s===r.entity}>
            ${this.hass.states[s].attributes.friendly_name??s}
          </option>`)}
        </select>
      </label>
      <label
        >${u(e,"card_editor_title")}
        <input type="text" .value=${r.title??""}
          @input=${s=>this._change({title:s.target.value||void 0})} />
      </label>
      <label class="check"
        ><input type="checkbox" .checked=${r.today!==!1}
          @change=${s=>this._change({today:s.target.checked})} />
        ${u(e,"card_editor_today")}</label
      >
    </div>`}};z.properties={hass:{attribute:!1},_config:{state:!0}},z.styles=k`
    .editor {
      display: grid;
      gap: 12px;
    }
    label {
      display: grid;
      gap: 4px;
      color: var(--secondary-text-color);
    }
    label.check {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    select,
    input[type="text"] {
      font: inherit;
      padding: 6px;
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 6px;
    }
  `;customElements.get(S)||customElements.define(S,U);customElements.get(ue)||customElements.define(ue,z);var Y=window;Y.customCards=Y.customCards??[];if(!Y.customCards.some(n=>n.type===S)){let n=q(navigator.language);Y.customCards.push({type:S,name:u(n,"card_name"),description:u(n,"card_description")})}export{U as WeishauptProgramCard,z as WeishauptProgramCardEditor};
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/lit-html.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-element/lit-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
